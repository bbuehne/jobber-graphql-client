"""Secure token manager for Jobber OAuth tokens.

Uses the system keyring for secure credential storage instead of files or environment variables.
This ensures tokens are stored securely at the OS level.

Extracted from ``jobber_mcp/auth/token_manager.py`` (PLAN-0027). Changes from the
source: the module-level ``settings`` fallback and the module-global
``token_manager`` singleton were removed — ``service_name`` is now a required
constructor argument (each consumer MUST use its own distinct service name;
see JobberClientConfig.keyring_service_name).
"""

import logging
from datetime import datetime, timedelta

from jobber_graphql_client.token_store import KeyringTokenStore, TokenStore

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages Jobber OAuth tokens with secure storage using system keyring.

    Stores access tokens, refresh tokens, and expiration times in the system's
    secure credential storage (Windows Credential Manager, macOS Keychain, etc).
    """

    def __init__(self, service_name: str, store: TokenStore | None = None):
        """Initialize token manager.

        Args:
            service_name: Service name for keyring. Consumers sharing a machine
                must each use a distinct name — Jobber rotates refresh tokens on
                use, so two processes sharing one stored token race each other.
            store: Where tokens live. Defaults to the OS keyring, which is what
                every existing consumer gets. A deployment that runs SEVERAL
                processes against ONE credential should pass a store whose
                ``supports_atomic_cas`` is true — the keyring cannot arbitrate
                concurrent writes, and that is how lighting-estimator lost its
                token on 2026-10-05.
        """
        self.service_name = service_name
        self.username = "jobber_oauth"  # Fixed username for Jobber tokens
        self._store: TokenStore = store or KeyringTokenStore(service_name, self.username)

    @property
    def store(self) -> TokenStore:
        """The backing store (read-only; set once at construction)."""
        return self._store

    def load_with_version(self) -> tuple[dict | None, int]:
        """Token payload plus the version to hand back to :meth:`store_tokens`.

        Read this BEFORE refreshing, and pass the version to the store on the
        way back in, so a peer that rotated meanwhile is not clobbered.
        """
        return self._store.load()

    def store_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: int | None = None,
        expected_version: int | None = None,
    ) -> bool:
        """Store OAuth tokens securely.

        Args:
            access_token: Jobber API access token
            refresh_token: Jobber API refresh token (optional)
            expires_in: Token expiration in seconds from now

        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate expiration time
            expiration_time = None
            if expires_in:
                expiration_time = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

            # Create token data structure
            token_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expiration_time,
                "stored_at": datetime.utcnow().isoformat(),
            }

            # Compare-and-swap when the caller read a version first; a blind
            # write otherwise (same behaviour consumers had before).
            if expected_version is None:
                _, expected_version = self._store.load()
            new_version = self._store.save(token_data, expected_version=expected_version)
            if new_version is None:
                # Someone else rotated first. Their token is newer and valid, so
                # this is a no-op rather than a failure — never overwrite it.
                logger.info("Jobber tokens already rotated by another process; kept theirs")
                return False

            logger.info("Jobber tokens stored securely")
            return True

        except Exception as e:
            logger.error(f"Failed to store tokens: {e}")
            return False

    def get_access_token(self) -> str | None:
        """Get stored access token.

        Returns:
            Access token if available and valid, None otherwise
        """
        try:
            token_data = self._get_token_data()
            if not token_data:
                return None

            # Check if expired
            if self._is_token_expired(token_data):
                logger.warning("Stored access token has expired")
                return None

            return token_data.get("access_token")

        except Exception as e:
            logger.error(f"Failed to retrieve access token: {e}")
            return None

    def get_refresh_token(self) -> str | None:
        """Get stored refresh token.

        Returns:
            Refresh token if available, None otherwise
        """
        try:
            token_data = self._get_token_data()
            if not token_data:
                return None

            return token_data.get("refresh_token")

        except Exception as e:
            logger.error(f"Failed to retrieve refresh token: {e}")
            return None

    def get_token_data(self) -> dict | None:
        """Get full token data (for internal use).

        Returns:
            Dictionary with access_token, refresh_token, expires_at, stored_at
        """
        return self._get_token_data()

    def is_authenticated(self) -> bool:
        """Check if tokens are stored and valid.

        Returns:
            True if valid access token is available
        """
        return self.get_access_token() is not None

    def is_token_expired(self) -> bool:
        """Check if stored token has expired.

        Returns:
            True if expired or not found, False if valid
        """
        try:
            token_data = self._get_token_data()
            if not token_data:
                return True

            return self._is_token_expired(token_data)

        except Exception:
            return True

    def clear_tokens(self) -> bool:
        """Clear all stored tokens.

        Returns:
            True if successful, False otherwise
        """
        # Only an explicit sign-out should reach here. A FAILED REFRESH must
        # never clear: with a rotating refresh token the loser of a race would
        # delete the winner's perfectly good credential (see token_store).
        if self._store.clear():
            logger.info("Jobber tokens cleared")
        return True

    def _get_token_data(self) -> dict | None:
        """Retrieve token data from keyring.

        Returns:
            Parsed token data or None if not found
        """
        data, _version = self._store.load()
        return data

    def _is_token_expired(self, token_data: dict) -> bool:
        """Check if token data has expired.

        Args:
            token_data: Token data dictionary

        Returns:
            True if expired, False if still valid
        """
        expires_at = token_data.get("expires_at")
        if not expires_at:
            # No expiration info, assume valid
            return False

        try:
            expiration_time = datetime.fromisoformat(expires_at)
            return datetime.utcnow() >= expiration_time

        except Exception as e:
            logger.warning(f"Failed to parse expiration time: {e}")
            return True

    def should_refresh_proactively(self) -> bool:
        """Check if token should be refreshed proactively before expiration.

        Refreshes if token expires within the next 5 minutes.
        This prevents API calls from failing due to expired tokens.

        Returns:
            True if token should be refreshed soon, False otherwise
        """
        try:
            token_data = self._get_token_data()
            if not token_data:
                return False

            expires_at = token_data.get("expires_at")
            if not expires_at:
                # No expiration info, don't need to refresh
                return False

            expiration_time = datetime.fromisoformat(expires_at)
            # Refresh if token expires within 5 minutes (300 seconds)
            refresh_threshold = datetime.utcnow() + timedelta(seconds=300)
            return expiration_time <= refresh_threshold

        except Exception as e:
            logger.warning(f"Failed to check proactive refresh: {e}")
            return False

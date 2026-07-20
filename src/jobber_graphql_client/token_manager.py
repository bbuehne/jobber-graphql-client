"""Secure token manager for Jobber OAuth tokens.

Uses the system keyring for secure credential storage instead of files or environment variables.
This ensures tokens are stored securely at the OS level.

Extracted from ``jobber_mcp/auth/token_manager.py`` (PLAN-0027). Changes from the
source: the module-level ``settings`` fallback and the module-global
``token_manager`` singleton were removed — ``service_name`` is now a required
constructor argument (each consumer MUST use its own distinct service name;
see JobberClientConfig.keyring_service_name).
"""

import json
import logging
from datetime import datetime, timedelta

import keyring
import keyring.errors

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages Jobber OAuth tokens with secure storage using system keyring.

    Stores access tokens, refresh tokens, and expiration times in the system's
    secure credential storage (Windows Credential Manager, macOS Keychain, etc).
    """

    def __init__(self, service_name: str):
        """Initialize token manager.

        Args:
            service_name: Service name for keyring. Consumers sharing a machine
                must each use a distinct name — Jobber rotates refresh tokens on
                use, so two processes sharing one stored token race each other.
        """
        self.service_name = service_name
        self.username = "jobber_oauth"  # Fixed username for Jobber tokens

    def store_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: int | None = None,
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

            # Store in keyring
            keyring.set_password(
                self.service_name,
                self.username,
                json.dumps(token_data),
            )

            logger.info("Jobber tokens stored securely in keyring")
            return True

        except Exception as e:
            logger.error(f"Failed to store tokens in keyring: {e}")
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
        try:
            keyring.delete_password(self.service_name, self.username)
            logger.info("Jobber tokens cleared from keyring")
            return True

        except keyring.errors.PasswordDeleteError:
            # Token wasn't stored, which is fine
            logger.debug("No stored tokens to clear")
            return True

        except Exception as e:
            logger.error(f"Failed to clear tokens: {e}")
            return False

    def _get_token_data(self) -> dict | None:
        """Retrieve token data from keyring.

        Returns:
            Parsed token data or None if not found
        """
        try:
            token_json = keyring.get_password(self.service_name, self.username)
            if not token_json:
                return None

            return json.loads(token_json)

        except Exception as e:
            logger.debug(f"Failed to get token data: {e}")
            return None

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

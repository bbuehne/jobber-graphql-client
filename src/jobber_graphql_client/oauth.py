"""Jobber OAuth 2.0 handler for API authentication.

Implements one-time OAuth setup for Jobber API access. Once tokens are obtained,
they are stored securely and automatically refreshed when needed.

Extracted from ``jobber_mcp/auth/jobber_oauth.py`` (PLAN-0027). Changes from the
source: the ``settings`` global and the module-global ``jobber_oauth`` singleton
were removed — configuration and the ``TokenManager`` are constructor-injected —
and the authorize URL's scope parameter is built from ``config.scopes`` instead
of the source's hard-coded scope list (which deliberately did not move).
"""

import asyncio
import logging

import httpx

from jobber_graphql_client.config import JobberClientConfig
from jobber_graphql_client.token_manager import TokenManager

logger = logging.getLogger(__name__)


class JobberOAuthHandler:
    """Handles Jobber OAuth 2.0 authentication and token management."""

    JOBBER_OAUTH_URL = "https://api.getjobber.com/api/oauth/authorize"
    JOBBER_TOKEN_URL = "https://api.getjobber.com/api/oauth/token"

    def __init__(self, config: JobberClientConfig, token_manager: TokenManager):
        """Initialize OAuth handler.

        Args:
            config: Client configuration (credentials, redirect URI, scopes)
            token_manager: Token store this handler reads/writes tokens through
        """
        self.client_id = config.jobber_client_id
        self.client_secret = config.jobber_client_secret
        self.redirect_uri = config.jobber_redirect_uri
        self.scopes = list(config.scopes)
        self._token_manager = token_manager
        self._refresh_lock = asyncio.Lock()

    def get_authorization_url(self, state: str) -> str:
        """Get Jobber OAuth authorization URL.

        Args:
            state: State parameter for CSRF protection

        Returns:
            Authorization URL
        """
        # Scopes come from config (JobberClientConfig.scopes), not a hard-coded list.
        # See: https://developer.getjobber.com/docs/oauth
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": " ".join(self.scopes),  # Join scopes with space
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.JOBBER_OAUTH_URL}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> dict | None:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Jobber

        Returns:
            Token response with access_token, refresh_token, expires_in
            None if exchange fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.JOBBER_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    timeout=10.0,
                )

            if response.status_code != 200:
                logger.error(f"Jobber token exchange failed: {response.text}")
                return None

            return response.json()

        except Exception as e:
            logger.error(f"Error exchanging code for Jobber token: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> dict | None:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Jobber refresh token

        Returns:
            Token response with new access_token, expires_in
            None if refresh fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.JOBBER_TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                    timeout=10.0,
                )

            if response.status_code != 200:
                logger.error(f"Jobber token refresh failed: {response.text}")
                return None

            return response.json()

        except Exception as e:
            logger.error(f"Error refreshing Jobber token: {e}")
            return None

    async def authenticate(self, code: str) -> bool:
        """Complete OAuth flow and store tokens.

        Args:
            code: Authorization code from Jobber

        Returns:
            True if successful, False otherwise
        """
        # Exchange code for token
        token_response = await self.exchange_code_for_token(code)
        if not token_response:
            logger.error("Failed to exchange Jobber authorization code")
            return False

        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in")

        if not access_token:
            logger.error("No access token in Jobber response")
            return False

        # Store tokens securely
        success = self._token_manager.store_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

        if success:
            logger.info("Jobber OAuth authentication successful")
        else:
            logger.error("Failed to store Jobber tokens")

        return success

    async def ensure_valid_token(self) -> str | None:
        """Ensure we have a valid access token, refreshing if needed.

        This method:
        1. Returns current token if valid and not expiring soon
        2. Proactively refreshes if token expires in next 5 minutes
        3. Refreshes if token has already expired
        4. Returns None if refresh fails

        Uses a lock to prevent concurrent refresh attempts which can
        invalidate refresh tokens (Jobber rotates refresh tokens on use).

        Returns:
            Valid access token or None if unavailable
        """
        # Fast path: check for valid, non-expiring token without lock
        if not self._token_manager.should_refresh_proactively():
            access_token = self._token_manager.get_access_token()
            if access_token:
                return access_token

        # Slow path: need to refresh, serialize with lock
        async with self._refresh_lock:
            # Re-check after acquiring lock (another coroutine may have refreshed)
            if not self._token_manager.should_refresh_proactively():
                access_token = self._token_manager.get_access_token()
                if access_token:
                    return access_token

            # Check for proactive refresh (before expiration)
            if self._token_manager.should_refresh_proactively():
                logger.info("Token expiring soon, performing proactive refresh...")
                refresh_token = self._token_manager.get_refresh_token()
                if refresh_token:
                    await self._refresh_and_store(refresh_token)
                    access_token = self._token_manager.get_access_token()
                    if access_token:
                        return access_token

            # Check if we have a stored access token
            access_token = self._token_manager.get_access_token()
            if access_token:
                return access_token

            # Try to refresh if we have a refresh token (token already expired)
            refresh_token = self._token_manager.get_refresh_token()
            if refresh_token:
                logger.info("Access token expired, attempting refresh...")
                await self._refresh_and_store(refresh_token)
                return self._token_manager.get_access_token()

        logger.error("No valid Jobber token available and refresh failed")
        return None

    async def _refresh_and_store(self, refresh_token: str) -> bool:
        """Refresh token and store new tokens securely.

        Args:
            refresh_token: The refresh token to use

        Returns:
            True if refresh succeeded, False otherwise
        """
        token_response = await self.refresh_access_token(refresh_token)

        if token_response:
            new_access_token = token_response.get("access_token")
            new_refresh_token = token_response.get("refresh_token", refresh_token)
            expires_in = token_response.get("expires_in")

            if new_access_token:
                # Store the new tokens
                success = self._token_manager.store_tokens(
                    access_token=new_access_token,
                    refresh_token=new_refresh_token,
                    expires_in=expires_in,
                )
                if success:
                    logger.info("Token refreshed successfully (proactive or reactive)")
                    return True

        return False

    def is_authenticated(self) -> bool:
        """Check if Jobber authentication is configured.

        Returns:
            True if valid tokens are stored
        """
        return self._token_manager.is_authenticated()

    def clear_authentication(self) -> bool:
        """Clear stored Jobber tokens.

        Returns:
            True if successful
        """
        return self._token_manager.clear_tokens()

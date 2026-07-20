"""GraphQL client for Jobber API with rate limiting and injectable caching.

Handles GraphQL queries, automatic rate limiting, token refresh,
and (optionally) response caching through an injected ResponseCache.

Extracted from ``jobber_mcp/api/client.py`` (PLAN-0027). Changes from the
source: the cache, OAuth handler, and token manager are constructor-injected
instance attributes instead of module-global imports (the four
``cache_service.X`` calls became ``self._cache.X``), endpoint/api version come
from an injected ``JobberClientConfig``, and the module-global
``graphql_client`` singleton was removed — each consumer constructs its own
client. Control flow inside ``execute()`` is otherwise identical to the source.
"""

import asyncio
import logging
from typing import Any

import httpx

from jobber_graphql_client.cache import NullCache, ResponseCache
from jobber_graphql_client.config import JobberClientConfig
from jobber_graphql_client.oauth import JobberOAuthHandler
from jobber_graphql_client.token_manager import TokenManager

logger = logging.getLogger(__name__)


class RateLimitInfo:
    """Tracks Jobber API rate limit state."""

    def __init__(self):
        """Initialize rate limit tracker."""
        self.current_points: int = 10000  # Assume full at start
        self.max_points: int = 10000
        self.restore_rate: int = 500  # Points restored per second

    def update_from_response(self, response_extensions: dict[str, Any]) -> None:
        """Update rate limit info from API response.

        Args:
            response_extensions: Extensions from GraphQL response
        """
        if not response_extensions:
            return

        throttle_info = response_extensions.get("throttle", {})
        if throttle_info:
            self.current_points = throttle_info.get("currentlyAvailable", self.current_points)
            self.max_points = throttle_info.get("maximumAvailable", self.max_points)
            self.restore_rate = throttle_info.get("restoreRate", self.restore_rate)

    async def wait_if_needed(self) -> None:
        """Wait if rate limit is low to avoid hitting limit.

        Waits if points are below 1000 (conservative threshold).
        """
        if self.current_points < 1000:
            wait_time = (1000 - self.current_points) / self.restore_rate
            logger.warning(
                f"Rate limit approaching ({self.current_points}/{self.max_points} points). "
                f"Waiting {wait_time:.2f}s..."
            )
            await asyncio.sleep(wait_time)

    def get_status(self) -> dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Dictionary with current points, max, and restore rate
        """
        return {
            "current_points": self.current_points,
            "max_points": self.max_points,
            "restore_rate": self.restore_rate,
            "percentage": (self.current_points / self.max_points * 100) if self.max_points else 0,
        }


class JobberGraphQLClient:
    """GraphQL client for Jobber API."""

    def __init__(
        self,
        config: JobberClientConfig,
        oauth: JobberOAuthHandler,
        token_manager: TokenManager,
        cache: ResponseCache | None = None,
    ):
        """Initialize GraphQL client.

        Args:
            config: Client configuration (endpoint, API version, ...)
            oauth: OAuth handler used to obtain/refresh access tokens
            token_manager: Token store (must be the same one ``oauth`` writes to)
            cache: Optional response cache; defaults to the no-op NullCache
        """
        self.endpoint = config.jobber_api_endpoint
        self.api_version = config.jobber_api_version
        self.rate_limit = RateLimitInfo()
        self._oauth = oauth
        self._token_manager = token_manager
        self._cache: ResponseCache = cache if cache is not None else NullCache()

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Execute a GraphQL query against Jobber API with automatic token refresh.

        Args:
            query: GraphQL query string
            variables: Variables for the query
            operation_name: Operation name (for multi-op documents)
            use_cache: Whether to use caching (default True, disabled for mutations)

        Returns:
            Response data from API
            Structure: {data: {...}, errors: [...], extensions: {...}}

        Raises:
            ValueError: If not authenticated
            httpx.HTTPError: If API request fails
        """
        # Check if this is a mutation (never cache mutations)
        is_mutation = query.strip().lower().startswith("mutation")

        # Try cache first for queries (not mutations)
        if use_cache and not is_mutation:
            cached = await self._cache.get(query, variables)
            if cached:
                logger.debug("Cache HIT - returning cached response")
                return cached

        # Attempt up to 2 times (initial + 1 retry after refresh)
        for attempt in range(2):
            try:
                # Ensure we have a valid token (with proactive refresh)
                access_token = await self._oauth.ensure_valid_token()
                if not access_token:
                    raise ValueError("Not authenticated with Jobber API")

                # Check rate limit before executing
                await self.rate_limit.wait_if_needed()

                # Prepare request
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "X-JOBBER-GRAPHQL-VERSION": self.api_version,
                    "Content-Type": "application/json",
                }

                payload: dict[str, Any] = {
                    "query": query,
                }

                if variables:
                    payload["variables"] = variables

                if operation_name:
                    payload["operationName"] = operation_name

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.endpoint,
                        json=payload,
                        headers=headers,
                    )

                # Handle HTTP errors
                if response.status_code == 401:
                    logger.warning(
                        f"Unauthorized (attempt {attempt + 1}): attempting token refresh..."
                    )

                    # First attempt - try to refresh token under lock to prevent races
                    if attempt == 0:
                        async with self._oauth._refresh_lock:
                            # Re-check token after acquiring lock - another coroutine
                            # may have refreshed
                            current_token = self._token_manager.get_access_token()
                            if current_token and current_token != access_token:
                                logger.info("Token was refreshed by another request, retrying...")
                                continue

                            refresh_token = self._token_manager.get_refresh_token()
                            if refresh_token:
                                logger.info("Attempting token refresh with stored refresh token...")
                                refreshed = await self._oauth._refresh_and_store(refresh_token)
                                if refreshed:
                                    logger.info("Token refresh successful, retrying request...")
                                    continue  # Retry the loop with new token
                                else:
                                    logger.warning("Token refresh failed, clearing authentication")
                            else:
                                logger.warning("No refresh token available")
                            # Clear tokens only after refresh attempt failed
                            self._oauth.clear_authentication()
                        continue  # One more attempt in case re-auth happened elsewhere
                    else:
                        # Second attempt failed, give up
                        logger.error("Jobber authentication failed after retry")
                        raise ValueError(
                            "Jobber authentication failed - please re-authenticate"
                            " at /auth/jobber/authorize"
                        )

                if response.status_code == 429:
                    logger.error("Rate limited by Jobber API")
                    raise RuntimeError("Rate limited by Jobber API")

                if response.status_code >= 400:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    raise RuntimeError(f"API error: {response.status_code}")

                # Parse response
                result = response.json()

                # Update rate limit from response
                extensions = result.get("extensions", {})
                self.rate_limit.update_from_response(extensions)

                # Log rate limit status
                status = self.rate_limit.get_status()
                logger.debug(
                    f"Rate limit: {status['current_points']}/{status['max_points']} points"
                )

                # Check for GraphQL errors
                if result.get("errors"):
                    errors = result.get("errors", [])
                    error_messages = [e.get("message", str(e)) for e in errors]
                    logger.error(f"GraphQL errors: {error_messages}")

                # Cache successful query responses (not mutations, not errors)
                if use_cache and not is_mutation and not result.get("errors"):
                    query_type = self._cache.detect_query_type(query)
                    await self._cache.set(query, variables, result, query_type)

                # Invalidate related cache on successful mutations
                if is_mutation and not result.get("errors"):
                    query_type = self._cache.detect_query_type(query)
                    if query_type != "default":
                        await self._cache.invalidate(query_type)

                return result

            except httpx.TimeoutException:
                logger.error("Request timeout calling Jobber API")
                raise

            except ValueError:
                # Re-raise authentication errors
                raise

            except Exception as e:
                logger.error(f"Error executing GraphQL query (attempt {attempt + 1}): {e}")
                if attempt == 1:
                    # Last attempt, raise the error
                    raise
                # First attempt, continue to retry

        raise RuntimeError("Failed to execute GraphQL query after retries")

    async def get_user_id(self) -> str | None:
        """Get current authenticated user's ID from Jobber.

        Useful for operations that require the current user ID.

        Returns:
            User ID if available, None otherwise
        """
        try:
            query = """
            query {
                user {
                    id
                }
            }
            """

            result = await self.execute(query)

            if result.get("errors"):
                return None

            data = result.get("data", {})
            return data.get("user", {}).get("id")

        except Exception as e:
            logger.warning(f"Failed to get user ID: {e}")
            return None

    def get_rate_limit_status(self) -> dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Dictionary with rate limit info
        """
        return self.rate_limit.get_status()

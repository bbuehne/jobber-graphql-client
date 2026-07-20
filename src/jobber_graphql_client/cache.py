"""Response-cache protocol for the Jobber GraphQL client.

The client does not know (or care) how responses are cached. Consumers inject
any object satisfying ``ResponseCache``; the default is ``NullCache``, a no-op
that behaves exactly like "caching disabled". The Jobber MCP injects its
Postgres-backed ``cache_service``; lighting-estimator injects ``NullCache``.

The four method signatures are derived from the actual call sites in the
original ``jobber_mcp/api/client.py`` (and match the concrete
``jobber_mcp.cache.CacheService`` implementation):

- ``await cache.get(query, variables)``
- ``await cache.set(query, variables, result, query_type)``
- ``await cache.invalidate(query_type)``
- ``cache.detect_query_type(query)`` (synchronous)
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ResponseCache(Protocol):
    """Protocol for GraphQL response caches injectable into the client."""

    async def get(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Return the cached response for (query, variables), or None on miss."""
        ...

    async def set(
        self,
        query: str,
        variables: dict[str, Any] | None,
        response: dict[str, Any],
        query_type: str | None = None,
    ) -> bool:
        """Store a response. Returns True if stored."""
        ...

    async def invalidate(self, query_type: str) -> int:
        """Invalidate all entries of a query type. Returns number removed."""
        ...

    def detect_query_type(self, query: str) -> str:
        """Classify a GraphQL document into a cache query type ('default' if unknown)."""
        ...


class NullCache:
    """No-op cache: semantically identical to running with caching disabled."""

    async def get(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Always miss."""
        return None

    async def set(
        self,
        query: str,
        variables: dict[str, Any] | None,
        response: dict[str, Any],
        query_type: str | None = None,
    ) -> bool:
        """Never store."""
        return False

    async def invalidate(self, query_type: str) -> int:
        """Nothing to invalidate."""
        return 0

    def detect_query_type(self, query: str) -> str:
        """Everything is 'default' (the type the client never invalidates)."""
        return "default"

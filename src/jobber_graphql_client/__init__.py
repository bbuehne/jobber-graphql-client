"""Shared Jobber GraphQL client.

Extracted from the Jobber MCP server per ADR-0006 / PLAN-0027 so that both the
Jobber MCP and lighting-estimator depend on one client stack. Query strings
live in :mod:`jobber_graphql_client.queries`.
"""

from jobber_graphql_client.cache import NullCache, ResponseCache
from jobber_graphql_client.client import JobberGraphQLClient, RateLimitInfo
from jobber_graphql_client.config import JobberClientConfig
from jobber_graphql_client.oauth import JobberOAuthHandler
from jobber_graphql_client.token_manager import TokenManager

__version__ = "0.1.0"

__all__ = [
    "JobberClientConfig",
    "JobberGraphQLClient",
    "JobberOAuthHandler",
    "NullCache",
    "RateLimitInfo",
    "ResponseCache",
    "TokenManager",
    "__version__",
]

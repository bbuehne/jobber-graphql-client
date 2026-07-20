# jobber-graphql-client

Shared Python client for the [Jobber GraphQL API](https://developer.getjobber.com/docs):
OAuth 2.0 (authorize / exchange / refresh), secure token storage in the OS keyring,
rate-limit tracking, and a `JobberGraphQLClient.execute()` that returns the raw
GraphQL envelope (`{data, errors, extensions}`) with automatic
401 → refresh-under-lock → retry handling. All Jobber query/mutation strings live in
`jobber_graphql_client.queries` — the single home for them.

## Who uses this

Two consumers, per ADR-0006 in the lighting-estimator repo (PLAN-0027):

1. **Jobber MCP server** (`bbuehne/jobber-mcp-server`) — injects its Postgres-backed
   response cache and re-exports a `graphql_client` singleton at the old dotted path
   so its tool modules are unchanged.
2. **lighting-estimator** (`bbuehne/lighting-estimator`) — injects `NullCache` (no
   caching, no database anywhere in this package) and holds its **own** keyring
   token under a **distinct** service name.

## Why a shared package (ADR-0006)

The client stack was extracted from the Jobber MCP because it was verified clean:
the only infrastructure coupling was the Postgres cache, now an injected
`ResponseCache` protocol with a `NullCache` no-op default. Vendoring was rejected
(guaranteed drift), MCP-to-MCP was rejected (formatted-text tools are brittle to
parse; no transactional control), model-orchestration was rejected (no atomicity
for writes). Dependencies are deliberately light: `httpx`, `keyring`, `pydantic` —
**no SQLAlchemy, no asyncpg, no Postgres**.

## Usage

```python
from jobber_graphql_client import (
    JobberClientConfig,
    JobberGraphQLClient,
    JobberOAuthHandler,
    NullCache,
    TokenManager,
)
from jobber_graphql_client.queries import GET_QUOTE_QUERY

config = JobberClientConfig(
    jobber_api_version="2025-04-16",
    jobber_client_id="...",
    jobber_client_secret="...",
    jobber_redirect_uri="https://example.com/oauth/jobber/callback",
    keyring_service_name="my-app-jobber",  # MUST be unique per consumer
    scopes=["clients:read", "quotes:write"],
)
token_manager = TokenManager(service_name=config.keyring_service_name)
oauth = JobberOAuthHandler(config, token_manager=token_manager)
client = JobberGraphQLClient(config, oauth=oauth, token_manager=token_manager,
                             cache=NullCache())

result = await client.execute(GET_QUOTE_QUERY, variables={"id": "..."})
```

The package never reads the environment: `JobberClientConfig` is a plain pydantic
model each application fills from its own settings.

**Token isolation is non-negotiable.** Jobber rotates refresh tokens on use and the
refresh lock is per-process only. Two processes sharing one keyring service name
will race each other into invalidated tokens. Every consumer picks its own
`keyring_service_name` and performs its own one-time OAuth.

## Version pinning policy

Consumers depend on this package as a **git dependency pinned to an exact tag**
(e.g. `v0.1.0`) — both consumers pin, nothing floats on `main`. Upgrades are an
explicit lockfile change in each consumer, taken independently.

## Development

Managed with [uv](https://docs.astral.sh/uv/):

```
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Tests use no network (httpx `MockTransport`) and no live keyring (in-memory
backend / injected fakes).

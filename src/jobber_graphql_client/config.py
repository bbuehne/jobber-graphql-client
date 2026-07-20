"""Client configuration for the shared Jobber GraphQL client.

A plain pydantic model (deliberately NOT BaseSettings, per PLAN-0027 §3): each
consuming application loads its own settings however it likes (env vars,
BaseSettings, config files) and constructs a ``JobberClientConfig`` from them.
The package itself never reads the environment.
"""

from pydantic import BaseModel


class JobberClientConfig(BaseModel):
    """Configuration required to talk to the Jobber GraphQL API.

    All fields except ``jobber_api_endpoint`` are required on purpose:

    - ``jobber_api_version`` is required so each consumer states explicitly
      which API version it is built against (no silent default drift).
    - ``keyring_service_name`` is required because the two consumers MUST use
      distinct keyring service names — Jobber rotates refresh tokens on use,
      and two processes sharing one stored token race each other into
      invalidation (PLAN-0027 §7 risk 1 / ADR-0006).
    - ``scopes`` is required; the OAuth authorize URL is built from this list.
      The hard-coded scope list in the original Jobber MCP source deliberately
      did not move into this package (PLAN-0027 §8.6).
    """

    jobber_api_endpoint: str = "https://api.getjobber.com/api/graphql"
    jobber_api_version: str
    jobber_client_id: str
    jobber_client_secret: str
    jobber_redirect_uri: str
    keyring_service_name: str
    scopes: list[str]

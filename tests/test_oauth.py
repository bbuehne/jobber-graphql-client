"""JobberOAuthHandler tests: config-driven scopes, token exchange/refresh.

No network (httpx.MockTransport) and no live keyring (FakeTokenManager).
"""

import httpx

from jobber_graphql_client.config import JobberClientConfig
from jobber_graphql_client.oauth import JobberOAuthHandler
from tests.conftest import FakeTokenManager


def make_handler(config, tm=None):
    tm = tm if tm is not None else FakeTokenManager()
    return JobberOAuthHandler(config, token_manager=tm), tm


def test_authorization_url_builds_scope_from_config(config):
    handler, _ = make_handler(config)
    url = handler.get_authorization_url(state="state-123")

    assert url.startswith("https://api.getjobber.com/api/oauth/authorize?")
    assert "client_id=test-client-id" in url
    assert "redirect_uri=https://example.test/oauth/jobber/callback" in url
    assert "response_type=code" in url
    assert "state=state-123" in url
    # Scope param comes from config.scopes, space-joined — not a hard-coded list.
    assert "scope=clients:read quotes:write" in url


def test_authorization_url_respects_custom_scopes():
    cfg = JobberClientConfig(
        jobber_api_version="2025-04-16",
        jobber_client_id="cid",
        jobber_client_secret="secret",
        jobber_redirect_uri="https://example.test/cb",
        keyring_service_name="svc",
        scopes=["account:read"],
    )
    handler, _ = make_handler(cfg)
    url = handler.get_authorization_url(state="s")
    assert "scope=account:read" in url
    # None of the old hard-coded extras sneak back in.
    assert "invoice:write" not in url


async def test_exchange_code_for_token(config, install_transport):
    seen = []

    def handler_fn(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={"access_token": "a1", "refresh_token": "r1", "expires_in": 3600},
        )

    install_transport(handler_fn)
    handler, _ = make_handler(config)

    result = await handler.exchange_code_for_token("code-1")

    assert result == {"access_token": "a1", "refresh_token": "r1", "expires_in": 3600}
    body = seen[0].content.decode()
    assert "grant_type=authorization_code" in body
    assert "code=code-1" in body
    assert "client_id=test-client-id" in body


async def test_exchange_code_failure_returns_none(config, install_transport):
    install_transport(lambda request: httpx.Response(400, text="bad code"))
    handler, _ = make_handler(config)
    assert await handler.exchange_code_for_token("nope") is None


async def test_authenticate_stores_tokens(config, install_transport):
    install_transport(
        lambda request: httpx.Response(
            200,
            json={"access_token": "a1", "refresh_token": "r1", "expires_in": 3600},
        )
    )
    handler, tm = make_handler(config, FakeTokenManager(access_token=None, refresh_token=None))

    assert await handler.authenticate("code-1") is True
    assert tm.access_token == "a1"
    assert tm.refresh_token == "r1"


async def test_refresh_and_store_keeps_old_refresh_token_if_absent(config, install_transport):
    """Jobber may omit refresh_token in a refresh response; the old one is kept."""
    install_transport(
        lambda request: httpx.Response(200, json={"access_token": "a2", "expires_in": 3600})
    )
    tm = FakeTokenManager(access_token="a1", refresh_token="r1")
    handler, _ = make_handler(config, tm)

    assert await handler._refresh_and_store("r1") is True
    assert tm.access_token == "a2"
    assert tm.refresh_token == "r1"  # preserved


async def test_refresh_and_store_rotates_refresh_token(config, install_transport):
    install_transport(
        lambda request: httpx.Response(
            200,
            json={"access_token": "a2", "refresh_token": "r2", "expires_in": 3600},
        )
    )
    tm = FakeTokenManager(access_token="a1", refresh_token="r1")
    handler, _ = make_handler(config, tm)

    assert await handler._refresh_and_store("r1") is True
    assert tm.refresh_token == "r2"


async def test_refresh_failure_returns_false(config, install_transport):
    install_transport(lambda request: httpx.Response(401, text="invalid refresh token"))
    tm = FakeTokenManager(access_token="a1", refresh_token="r1")
    handler, _ = make_handler(config, tm)

    assert await handler._refresh_and_store("r1") is False
    assert tm.access_token == "a1"  # unchanged


async def test_ensure_valid_token_fast_path(config, install_transport):
    """A valid, non-expiring token is returned without any HTTP traffic."""
    calls = []

    def handler_fn(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={})

    install_transport(handler_fn)

    class TM(FakeTokenManager):
        def should_refresh_proactively(self) -> bool:
            return False

    tm = TM(access_token="a1")
    handler, _ = make_handler(config, tm)

    assert await handler.ensure_valid_token() == "a1"
    assert calls == []


async def test_ensure_valid_token_refreshes_expired_token(config, install_transport):
    install_transport(
        lambda request: httpx.Response(
            200,
            json={"access_token": "a2", "refresh_token": "r2", "expires_in": 3600},
        )
    )

    class TM(FakeTokenManager):
        def should_refresh_proactively(self) -> bool:
            # Expired token: no proactive window, no access token, refresh only.
            return False

    tm = TM(access_token=None, refresh_token="r1")
    handler, _ = make_handler(config, tm)

    assert await handler.ensure_valid_token() == "a2"
    assert tm.refresh_token == "r2"

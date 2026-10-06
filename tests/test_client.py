"""Behavior tests for JobberGraphQLClient with injected fakes.

Covers: success path, error-envelope passthrough, rate-limit parsing,
cache hit/set/invalidate behavior, and the 401 -> refresh-under-lock ->
retry path. No network: HTTP is served by httpx.MockTransport.
"""

import httpx
import pytest

from jobber_graphql_client.client import JobberGraphQLClient, RateLimitInfo
from tests.conftest import FakeCache, FakeOAuth, FakeTokenManager

QUERY = "query GetThing { thing { id } }"
MUTATION = "mutation EditThing { thingEdit { thing { id } } }"

SUCCESS_BODY = {
    "data": {"thing": {"id": "T1"}},
    "extensions": {
        "cost": {
            "throttleStatus": {},
        },
        "throttle": {
            "currentlyAvailable": 9000,
            "maximumAvailable": 10000,
            "restoreRate": 500,
        },
    },
}


def make_client(config, cache=None, oauth=None, tm=None):
    tm = tm if tm is not None else FakeTokenManager()
    oauth = oauth if oauth is not None else FakeOAuth(tm)
    client = JobberGraphQLClient(config, oauth=oauth, token_manager=tm, cache=cache)
    return client, oauth, tm


async def test_success_path_payload_headers_and_cache_set(config, install_transport):
    """Happy path: correct payload/headers sent, envelope returned, response cached."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=SUCCESS_BODY)

    install_transport(handler)
    cache = FakeCache(query_type="things")
    client, _, _ = make_client(config, cache=cache)

    result = await client.execute(QUERY, variables={"a": 1}, operation_name="GetThing")

    assert result == SUCCESS_BODY
    assert len(requests) == 1
    req = requests[0]
    assert str(req.url) == config.jobber_api_endpoint
    assert req.headers["Authorization"] == "Bearer token-1"
    assert req.headers["X-JOBBER-GRAPHQL-VERSION"] == "2025-04-16"
    assert req.headers["Content-Type"] == "application/json"
    import json

    payload = json.loads(req.content)
    assert payload == {"query": QUERY, "variables": {"a": 1}, "operationName": "GetThing"}

    # Cached exactly once, with the detected query type
    assert cache.get_calls == [(QUERY, {"a": 1})]
    assert cache.set_calls == [(QUERY, {"a": 1}, SUCCESS_BODY, "things")]
    assert cache.invalidate_calls == []


async def test_error_envelope_passthrough_not_cached(config, install_transport):
    """A 200 response with GraphQL errors is returned verbatim and never cached."""
    body = {
        "data": None,
        "errors": [{"message": "Not found", "path": ["thing"]}],
        "extensions": {"requestId": "abc"},
    }
    install_transport(lambda request: httpx.Response(200, json=body))
    cache = FakeCache(query_type="things")
    client, _, _ = make_client(config, cache=cache)

    result = await client.execute(QUERY)

    assert result == body  # {data, errors, extensions} passed through untouched
    assert cache.set_calls == []
    assert cache.invalidate_calls == []


async def test_rate_limit_info_parsed_from_extensions(config, install_transport):
    install_transport(lambda request: httpx.Response(200, json=SUCCESS_BODY))
    client, _, _ = make_client(config)

    await client.execute(QUERY, use_cache=False)

    status = client.get_rate_limit_status()
    assert status["current_points"] == 9000
    assert status["max_points"] == 10000
    assert status["restore_rate"] == 500
    assert status["percentage"] == 90.0


def test_rate_limit_info_ignores_missing_throttle():
    info = RateLimitInfo()
    info.update_from_response({})
    info.update_from_response({"cost": {}})
    assert info.get_status()["current_points"] == 10000


async def test_cache_hit_skips_http(config, install_transport):
    cached_body = {"data": {"thing": {"id": "cached"}}}
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=SUCCESS_BODY)

    install_transport(handler)
    cache = FakeCache(cached=cached_body)
    client, _, _ = make_client(config, cache=cache)

    result = await client.execute(QUERY)

    assert result == cached_body
    assert calls == []  # no HTTP request made


async def test_use_cache_false_bypasses_cache(config, install_transport):
    install_transport(lambda request: httpx.Response(200, json=SUCCESS_BODY))
    cache = FakeCache(cached={"data": {"thing": {"id": "cached"}}})
    client, _, _ = make_client(config, cache=cache)

    result = await client.execute(QUERY, use_cache=False)

    assert result == SUCCESS_BODY
    assert cache.get_calls == []
    assert cache.set_calls == []


async def test_mutation_never_cached_and_invalidates(config, install_transport):
    install_transport(lambda request: httpx.Response(200, json={"data": {"ok": True}}))
    cache = FakeCache(query_type="things")
    client, _, _ = make_client(config, cache=cache)

    await client.execute(MUTATION)

    assert cache.get_calls == []
    assert cache.set_calls == []
    assert cache.invalidate_calls == ["things"]


async def test_mutation_with_default_type_not_invalidated(config, install_transport):
    install_transport(lambda request: httpx.Response(200, json={"data": {"ok": True}}))
    cache = FakeCache(query_type="default")
    client, _, _ = make_client(config, cache=cache)

    await client.execute(MUTATION)

    assert cache.invalidate_calls == []


async def test_failed_mutation_does_not_invalidate(config, install_transport):
    body = {"data": None, "errors": [{"message": "boom"}]}
    install_transport(lambda request: httpx.Response(200, json=body))
    cache = FakeCache(query_type="things")
    client, _, _ = make_client(config, cache=cache)

    result = await client.execute(MUTATION)

    assert result == body
    assert cache.invalidate_calls == []


async def test_401_refresh_under_lock_then_retry(config, install_transport):
    """First request 401s; refresh succeeds under the oauth lock; retry succeeds."""
    seen_auth: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_auth.append(request.headers["Authorization"])
        if request.headers["Authorization"] == "Bearer token-1":
            return httpx.Response(401, json={"error": "unauthorized"})
        return httpx.Response(200, json=SUCCESS_BODY)

    install_transport(handler)
    tm = FakeTokenManager(access_token="token-1", refresh_token="refresh-1")
    oauth = FakeOAuth(tm, refresh_ok=True)
    client, _, _ = make_client(config, oauth=oauth, tm=tm)

    result = await client.execute(QUERY, use_cache=False)

    assert result == SUCCESS_BODY
    assert oauth.refresh_calls == ["refresh-1"]
    assert seen_auth == ["Bearer token-1", "Bearer refreshed-token"]
    assert oauth.cleared is False


async def test_401_token_already_refreshed_by_other_request(config, install_transport):
    """If another coroutine refreshed while we waited on the lock, retry without refreshing."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers["Authorization"] == "Bearer stale-token":
            return httpx.Response(401, json={"error": "unauthorized"})
        return httpx.Response(200, json=SUCCESS_BODY)

    install_transport(handler)
    tm = FakeTokenManager(access_token="stale-token", refresh_token="refresh-1")
    oauth = FakeOAuth(tm, refresh_ok=True)

    # Simulate the concurrent refresh: by the time the client re-checks the
    # token manager under the lock, the stored token differs from the one used.
    original_get = tm.get_access_token
    state = {"first": True}

    def get_access_token():
        if state["first"]:
            state["first"] = False
            return original_get()
        return "other-token"

    tm.get_access_token = get_access_token  # type: ignore[method-assign]
    client, _, _ = make_client(config, oauth=oauth, tm=tm)

    result = await client.execute(QUERY, use_cache=False)

    assert result == SUCCESS_BODY
    assert oauth.refresh_calls == []  # no refresh performed by this client


async def test_401_refresh_failure_does_not_clear_auth(config, install_transport):
    """A failed refresh must NEVER delete the stored credential.

    Jobber rotates the refresh token on every use, so when several processes
    share one credential the loser of a race is rejected while the WINNER has
    just stored a perfectly good token. Deleting on that failure destroys the
    winner's token and turns a recoverable blip into an outage needing a human
    to re-authorise.

    That is not hypothetical: it took lighting-estimator's tour typeahead,
    nightly backfill and MCP connector sign-ins down on 2026-10-05, six minutes
    after a deploy restart.

    It still raises — the caller's request genuinely cannot be served — but it
    leaves the credential alone.
    """
    install_transport(lambda request: httpx.Response(401, json={"error": "unauthorized"}))
    tm = FakeTokenManager(access_token="token-1", refresh_token="refresh-1")
    oauth = FakeOAuth(tm, refresh_ok=False)

    async def always_token():
        return "token-1"

    oauth.ensure_valid_token = always_token  # type: ignore[method-assign]
    client, _, _ = make_client(config, oauth=oauth, tm=tm)

    with pytest.raises(ValueError, match="re-authenticate"):
        await client.execute(QUERY, use_cache=False)

    assert oauth.refresh_calls == ["refresh-1"]
    assert oauth.cleared is False, "a failed refresh deleted the credential"


async def test_not_authenticated_raises_value_error(config, install_transport):
    install_transport(lambda request: httpx.Response(200, json=SUCCESS_BODY))
    tm = FakeTokenManager(access_token=None, refresh_token=None)
    oauth = FakeOAuth(tm)
    client, _, _ = make_client(config, oauth=oauth, tm=tm)

    with pytest.raises(ValueError, match="Not authenticated"):
        await client.execute(QUERY, use_cache=False)


async def test_http_429_raises_runtime_error(config, install_transport):
    install_transport(lambda request: httpx.Response(429, json={}))
    client, _, _ = make_client(config)

    with pytest.raises(RuntimeError, match="Rate limited"):
        await client.execute(QUERY, use_cache=False)


async def test_http_500_retries_then_raises(config, install_transport):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(500, text="boom")

    install_transport(handler)
    client, _, _ = make_client(config)

    with pytest.raises(RuntimeError, match="API error: 500"):
        await client.execute(QUERY, use_cache=False)

    # Non-auth exceptions are retried once (source behavior: generic except
    # continues on attempt 0, re-raises on attempt 1).
    assert len(calls) == 2


async def test_default_cache_is_nullcache(config, install_transport):
    install_transport(lambda request: httpx.Response(200, json=SUCCESS_BODY))
    tm = FakeTokenManager()
    client = JobberGraphQLClient(config, oauth=FakeOAuth(tm), token_manager=tm)

    from jobber_graphql_client.cache import NullCache

    assert isinstance(client._cache, NullCache)
    assert await client.execute(QUERY) == SUCCESS_BODY

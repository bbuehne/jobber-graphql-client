"""Shared fakes and fixtures.

No network, no live keyring: HTTP goes through httpx.MockTransport (installed
by monkeypatching httpx.AsyncClient as seen from the package modules), and
keyring tests use an in-memory backend (see test_token_manager.py).
"""

import asyncio
from typing import Any

import httpx
import pytest

from jobber_graphql_client.config import JobberClientConfig


class FakeCache:
    """Recording fake satisfying the ResponseCache protocol."""

    def __init__(
        self,
        cached: dict[str, Any] | None = None,
        query_type: str = "default",
    ):
        self.cached = cached
        self.query_type = query_type
        self.get_calls: list[tuple[str, dict[str, Any] | None]] = []
        self.set_calls: list[tuple[str, dict[str, Any] | None, dict[str, Any], str | None]] = []
        self.invalidate_calls: list[str] = []
        self.detect_calls: list[str] = []

    async def get(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        self.get_calls.append((query, variables))
        return self.cached

    async def set(
        self,
        query: str,
        variables: dict[str, Any] | None,
        response: dict[str, Any],
        query_type: str | None = None,
    ) -> bool:
        self.set_calls.append((query, variables, response, query_type))
        return True

    async def invalidate(self, query_type: str) -> int:
        self.invalidate_calls.append(query_type)
        return 1

    def detect_query_type(self, query: str) -> str:
        self.detect_calls.append(query)
        return self.query_type


class FakeTokenManager:
    """In-memory stand-in for TokenManager (no keyring)."""

    def __init__(
        self,
        access_token: str | None = "token-1",
        refresh_token: str | None = "refresh-1",
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token

    def get_access_token(self) -> str | None:
        return self.access_token

    def get_refresh_token(self) -> str | None:
        return self.refresh_token

    def store_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: int | None = None,
    ) -> bool:
        self.access_token = access_token
        self.refresh_token = refresh_token
        return True

    def clear_tokens(self) -> bool:
        self.access_token = None
        self.refresh_token = None
        return True


class FakeOAuth:
    """Stand-in for JobberOAuthHandler wired to a FakeTokenManager.

    Exposes exactly the surface the client uses: ensure_valid_token,
    _refresh_lock, _refresh_and_store, clear_authentication.
    """

    def __init__(self, token_manager: FakeTokenManager, refresh_ok: bool = True):
        self._tm = token_manager
        self._refresh_lock = asyncio.Lock()
        self.refresh_ok = refresh_ok
        self.refresh_calls: list[str] = []
        self.cleared = False

    async def ensure_valid_token(self) -> str | None:
        return self._tm.get_access_token()

    async def _refresh_and_store(self, refresh_token: str) -> bool:
        self.refresh_calls.append(refresh_token)
        if self.refresh_ok:
            self._tm.store_tokens("refreshed-token", "refresh-2", 3600)
            return True
        return False

    def clear_authentication(self) -> bool:
        self.cleared = True
        return self._tm.clear_tokens()


@pytest.fixture
def config() -> JobberClientConfig:
    return JobberClientConfig(
        jobber_api_version="2025-04-16",
        jobber_client_id="test-client-id",
        jobber_client_secret="test-client-secret",
        jobber_redirect_uri="https://example.test/oauth/jobber/callback",
        keyring_service_name="jobber-graphql-client-tests",
        scopes=["clients:read", "quotes:write"],
    )


@pytest.fixture
def install_transport(monkeypatch):
    """Route all httpx.AsyncClient traffic through a MockTransport handler.

    The client and oauth modules construct httpx.AsyncClient(...) internally
    (no transport parameter in their signatures — kept identical to the
    source), so tests patch the AsyncClient constructor to inject a
    MockTransport. monkeypatch restores the real class after each test.
    """
    real_async_client = httpx.AsyncClient

    def _install(handler) -> None:
        def factory(**kwargs: Any) -> httpx.AsyncClient:
            kwargs["transport"] = httpx.MockTransport(handler)
            return real_async_client(**kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", factory)

    return _install

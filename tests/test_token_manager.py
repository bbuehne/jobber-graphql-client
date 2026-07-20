"""TokenManager tests against an in-memory keyring backend (no live keyring)."""

from datetime import datetime, timedelta

import keyring
import keyring.backend
import keyring.errors
import pytest

from jobber_graphql_client.token_manager import TokenManager


class InMemoryKeyring(keyring.backend.KeyringBackend):
    """Minimal in-memory keyring backend for tests."""

    priority = 1

    def __init__(self) -> None:
        super().__init__()
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        if (service, username) not in self.store:
            raise keyring.errors.PasswordDeleteError("no such password")
        del self.store[(service, username)]


@pytest.fixture
def mem_keyring():
    backend = InMemoryKeyring()
    previous = keyring.get_keyring()
    keyring.set_keyring(backend)
    try:
        yield backend
    finally:
        keyring.set_keyring(previous)


@pytest.fixture
def tm(mem_keyring) -> TokenManager:
    return TokenManager(service_name="tm-tests")


def test_store_and_get_round_trip(tm):
    assert tm.store_tokens("access-1", "refresh-1", expires_in=3600) is True
    assert tm.get_access_token() == "access-1"
    assert tm.get_refresh_token() == "refresh-1"
    assert tm.is_authenticated() is True
    assert tm.is_token_expired() is False


def test_get_access_token_when_nothing_stored(tm):
    assert tm.get_access_token() is None
    assert tm.get_refresh_token() is None
    assert tm.is_authenticated() is False
    assert tm.is_token_expired() is True


def test_expired_access_token_returns_none_but_refresh_survives(tm, mem_keyring):
    tm.store_tokens("access-1", "refresh-1", expires_in=3600)
    # Rewrite the stored expiry into the past.
    import json

    key = (tm.service_name, tm.username)
    data = json.loads(mem_keyring.store[key])
    data["expires_at"] = (datetime.utcnow() - timedelta(seconds=10)).isoformat()
    mem_keyring.store[key] = json.dumps(data)

    assert tm.get_access_token() is None
    assert tm.get_refresh_token() == "refresh-1"
    assert tm.is_token_expired() is True


def test_no_expiry_means_valid(tm):
    tm.store_tokens("access-1", "refresh-1", expires_in=None)
    assert tm.get_access_token() == "access-1"
    assert tm.is_token_expired() is False
    assert tm.should_refresh_proactively() is False


def test_should_refresh_proactively_near_expiry(tm):
    tm.store_tokens("access-1", "refresh-1", expires_in=60)  # inside 5-min window
    assert tm.should_refresh_proactively() is True

    tm.store_tokens("access-2", "refresh-2", expires_in=3600)  # far from expiry
    assert tm.should_refresh_proactively() is False


def test_clear_tokens(tm):
    tm.store_tokens("access-1", "refresh-1", expires_in=3600)
    assert tm.clear_tokens() is True
    assert tm.get_access_token() is None
    # Clearing when nothing is stored is fine (PasswordDeleteError swallowed).
    assert tm.clear_tokens() is True


def test_distinct_service_names_are_isolated(mem_keyring):
    """The two consumers must not see each other's tokens (PLAN-0027 risk 1)."""
    mcp = TokenManager(service_name="jobber-mcp-server")
    estimator = TokenManager(service_name="lighting-estimator-jobber")

    mcp.store_tokens("mcp-access", "mcp-refresh", expires_in=3600)
    estimator.store_tokens("est-access", "est-refresh", expires_in=3600)

    assert mcp.get_access_token() == "mcp-access"
    assert estimator.get_access_token() == "est-access"

    estimator.clear_tokens()
    assert mcp.get_access_token() == "mcp-access"
    assert estimator.get_access_token() is None

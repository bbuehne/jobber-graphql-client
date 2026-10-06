"""Tests for the token store seam and its compare-and-swap contract.

These exist because of a real outage. On 2026-10-05 lighting-estimator's three
processes — admin app, MCP server, nightly backfill — raced each other on one
rotating Jobber refresh token. Six minutes after a deploy restart the stored
credential was invalid and stayed that way until a human re-authorised, taking
out the tour typeahead, the backfill, and MCP connector sign-ins.
"""

from __future__ import annotations

import pytest

from jobber_graphql_client.token_manager import TokenManager
from jobber_graphql_client.token_store import CONFLICT, TokenStore


class InMemoryStore:
    """An atomic store, standing in for the database-backed one."""

    def __init__(self) -> None:
        self.data: dict | None = None
        self.version = 0
        self.clears = 0

    @property
    def supports_atomic_cas(self) -> bool:
        return True

    def load(self) -> tuple[dict | None, int]:
        return (dict(self.data) if self.data is not None else None), self.version

    def save(self, token_data: dict, *, expected_version: int) -> int | None:
        if expected_version != self.version:
            return CONFLICT
        self.data = dict(token_data)
        self.version += 1
        return self.version

    def clear(self) -> bool:
        self.clears += 1
        self.data = None
        self.version += 1
        return True


def test_in_memory_store_satisfies_the_protocol() -> None:
    assert isinstance(InMemoryStore(), TokenStore)


# --------------------------------------------------------------------------- #
# The race this change exists to prevent
# --------------------------------------------------------------------------- #


def test_second_writer_does_not_clobber_the_first() -> None:
    """Two processes read the same version; only one write may land.

    This is the Oct 5 shape: both read, both refresh, both try to store. The
    loser must leave the winner's token alone.
    """
    store = InMemoryStore()
    store.save({"access_token": "original"}, expected_version=0)

    _, version_a = store.load()  # process A reads
    _, version_b = store.load()  # process B reads the SAME version

    assert store.save({"access_token": "from-A"}, expected_version=version_a) is not CONFLICT
    assert store.save({"access_token": "from-B"}, expected_version=version_b) is CONFLICT

    data, _ = store.load()
    assert data == {"access_token": "from-A"}, "the loser overwrote the winner"


def test_conflict_is_not_an_error_and_leaves_a_usable_token() -> None:
    """A conflict means a peer already stored something newer and valid."""
    store = InMemoryStore()
    manager = TokenManager("test-service", store=store)

    manager.store_tokens(access_token="first", refresh_token="r1", expires_in=3600)
    _, stale_version = (None, 0)  # a version read before the write above

    stored = manager.store_tokens(
        access_token="second",
        refresh_token="r2",
        expires_in=3600,
        expected_version=stale_version,
    )

    assert stored is False
    assert manager.get_access_token() == "first"


def test_version_advances_on_every_successful_write() -> None:
    store = InMemoryStore()
    manager = TokenManager("test-service", store=store)

    versions = []
    for index in range(3):
        manager.store_tokens(access_token=f"t{index}", refresh_token="r", expires_in=3600)
        _, version = manager.load_with_version()
        versions.append(version)

    assert versions == sorted(set(versions)), f"versions did not advance: {versions}"


# --------------------------------------------------------------------------- #
# Reads and clears route through the store
# --------------------------------------------------------------------------- #


def test_manager_reads_through_the_store() -> None:
    store = InMemoryStore()
    manager = TokenManager("test-service", store=store)
    manager.store_tokens(access_token="abc", refresh_token="ref", expires_in=3600)

    assert manager.get_access_token() == "abc"
    assert manager.get_refresh_token() == "ref"
    assert manager.is_authenticated() is True


def test_clear_is_explicit_only() -> None:
    """clear_tokens is sign-out. Nothing in the refresh path may call it."""
    store = InMemoryStore()
    manager = TokenManager("test-service", store=store)
    manager.store_tokens(access_token="abc", refresh_token="ref", expires_in=3600)

    manager.clear_tokens()

    assert store.clears == 1
    assert manager.get_access_token() is None


def test_keyring_store_is_honest_about_not_being_atomic() -> None:
    """It narrows the race; it cannot close it. Say so rather than imply safety."""
    from jobber_graphql_client.token_store import KeyringTokenStore

    assert KeyringTokenStore("svc").supports_atomic_cas is False


def test_default_manager_still_uses_the_keyring() -> None:
    """Existing consumers must keep working with no code change."""
    from jobber_graphql_client.token_store import KeyringTokenStore

    manager = TokenManager("test-service")

    assert isinstance(manager.store, KeyringTokenStore)


@pytest.mark.parametrize("missing", [None, {}])
def test_absent_token_reads_as_unauthenticated(missing) -> None:
    store = InMemoryStore()
    store.data = missing
    manager = TokenManager("test-service", store=store)

    assert manager.get_access_token() is None
    assert manager.is_authenticated() is False

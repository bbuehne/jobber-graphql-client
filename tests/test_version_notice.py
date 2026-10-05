"""Tests for ``log_version_notice`` — Jobber's API-version deprecation warning.

Why this exists: before this, ``extensions`` from every GraphQL response was
handed only to the rate-limit tracker, which reads only ``extensions["throttle"]``.
The ``versioning`` key — Jobber's sole advance notice that a pinned version is
about to become inaccessible, after which requests are silently upgraded to the
oldest supported version — was dropped on the floor.
"""

from __future__ import annotations

import logging

import pytest

from jobber_graphql_client import client as client_module
from jobber_graphql_client.client import log_version_notice

# A real-shaped payload, matching the example in Jobber's versioning docs.
NOTICE = {
    "versioning": {
        "version": "2025-04-16",
        "warning": (
            "Support for API version 2025-04-16 is scheduled to stop on "
            "April 16, 2026. Upgrade to the latest version 2026-09-25 before "
            "that date."
        ),
    }
}


@pytest.fixture(autouse=True)
def _clear_dedupe_cache():
    """The dedupe set is module state; isolate each test from the others."""
    client_module._seen_version_notices.clear()
    yield
    client_module._seen_version_notices.clear()


def test_logs_the_warning_with_the_served_version(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger=client_module.__name__):
        log_version_notice(NOTICE)

    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert "2025-04-16" in message
    assert "2026-09-25" in message
    assert "Jobber API version notice" in message


def test_same_notice_logs_once_per_process(caplog) -> None:
    """The nightly backfill makes hundreds of calls; one notice is enough."""
    with caplog.at_level(logging.WARNING, logger=client_module.__name__):
        for _ in range(50):
            log_version_notice(NOTICE)

    assert len(caplog.records) == 1


def test_a_different_notice_still_gets_through(caplog) -> None:
    """Dedupe is per distinct warning text, not "warn once and go quiet"."""
    escalated = {
        "versioning": {
            "version": "2025-04-16",
            "warning": "API version 2025-04-16 is unsupported and can be removed at any time.",
        }
    }
    with caplog.at_level(logging.WARNING, logger=client_module.__name__):
        log_version_notice(NOTICE)
        log_version_notice(escalated)

    assert len(caplog.records) == 2
    assert "unsupported" in caplog.records[1].getMessage()


def test_version_without_a_warning_is_silent(caplog) -> None:
    """A healthy, current version reports its version and no warning."""
    with caplog.at_level(logging.WARNING, logger=client_module.__name__):
        log_version_notice({"versioning": {"version": "2026-09-25"}})

    assert caplog.records == []


@pytest.mark.parametrize(
    "extensions",
    [
        {},
        None,
        {"throttle": {"currentlyAvailable": 9000}},
        {"versioning": None},
        {"versioning": {}},
    ],
    ids=["empty", "none", "throttle-only", "versioning-null", "versioning-empty"],
)
def test_tolerates_payloads_without_a_notice(extensions, caplog) -> None:
    """Must never raise on a response shape it did not expect."""
    with caplog.at_level(logging.WARNING, logger=client_module.__name__):
        log_version_notice(extensions)

    assert caplog.records == []


def test_rate_limit_handling_is_unaffected() -> None:
    """The throttle path must keep working exactly as before."""
    rate_limit = client_module.RateLimitInfo()
    rate_limit.update_from_response(
        {
            "throttle": {
                "currentlyAvailable": 4200,
                "maximumAvailable": 10000,
                "restoreRate": 500,
            },
            "versioning": NOTICE["versioning"],
        }
    )

    assert rate_limit.current_points == 4200
    assert rate_limit.max_points == 10000
    assert rate_limit.restore_rate == 500

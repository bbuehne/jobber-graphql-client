"""Where the Jobber OAuth tokens live, and how two processes share them safely.

Jobber **rotates the refresh token on every use**: refreshing with R1 returns
R2 and immediately invalidates R1. That is fine for one process and hostile to
several, and lighting-estimator runs three that share one credential — the
admin app, the MCP server, and the nightly backfill oneshot.

On 2026-10-05 that bit: six minutes after a deploy restart the stored refresh
token was invalid, and it stayed invalid until a human re-authorised. It took
down the tour typeahead, the nightly backfill, and new MCP connector sign-ins.

Two defects combined:

1. **No coordination across processes.** The only guard was an ``asyncio.Lock``
   on the OAuth handler, which serialises refreshes *within* one process and
   does nothing between them.
2. **A failed refresh deleted the credential.** When the loser of a race was
   rejected, it called ``clear_authentication()`` — destroying the good token
   the winner had just written, and converting a recoverable blip into an
   outage needing a human.

This module fixes (1) by making a store's write a **compare-and-swap** against
a version the caller has already read. A store that cannot do that atomically
says so, rather than pretending.

(2) is fixed in ``client.py``: a failed refresh now re-reads the store and uses
whatever another process may have stored, and **never deletes**.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol, runtime_checkable

import keyring
import keyring.errors

logger = logging.getLogger(__name__)

#: Returned by :meth:`TokenStore.save` when the stored version moved underneath
#: us — another process rotated the token first. Not an error: the caller
#: should re-read and use the winner's token.
CONFLICT: None = None


@runtime_checkable
class TokenStore(Protocol):
    """Somewhere a Jobber token lives, with enough structure to rotate safely.

    The token payload is the dict ``TokenManager`` already uses:
    ``{access_token, refresh_token, expires_at, stored_at}``. A store neither
    inspects nor validates it — it persists bytes and arbitrates writes.
    """

    def load(self) -> tuple[dict | None, int]:
        """Return ``(token_data, version)``; ``(None, 0)`` when nothing stored.

        The version is opaque to callers except that it must be passed back to
        :meth:`save` unchanged, and that it changes on every successful write.
        """
        ...

    def save(self, token_data: dict, *, expected_version: int) -> int | None:
        """Write ``token_data`` only if the stored version is still
        ``expected_version``.

        Returns the new version on success, or :data:`CONFLICT` (``None``) when
        someone else wrote first. A conflict is **not** a failure — it means a
        peer already has a newer, valid token and the caller should re-read.
        """
        ...

    def clear(self) -> bool:
        """Delete the stored token. Used by explicit sign-out, never by a
        failed refresh."""
        ...

    @property
    def supports_atomic_cas(self) -> bool:
        """Whether :meth:`save` is genuinely atomic against concurrent writers.

        ``False`` means the version check narrows the race but cannot close it,
        and callers should not claim otherwise in logs or docs.
        """
        ...


class KeyringTokenStore:
    """The historical store: one JSON blob in the OS keyring.

    **Not atomic.** The keyring offers no compare-and-swap, so the version is
    carried inside the stored JSON and checked read-then-write. That narrows
    the window — a writer that notices a version bump backs off instead of
    clobbering — but two processes can still interleave between the read and
    the write.

    This remains the default so existing consumers keep working unchanged. A
    deployment that actually runs several processes against one credential
    should supply a store whose ``supports_atomic_cas`` is ``True`` (for
    lighting-estimator, the database-backed one).
    """

    #: Key the version is kept under inside the stored JSON.
    VERSION_KEY = "_version"

    def __init__(self, service_name: str, username: str = "jobber_oauth") -> None:
        self.service_name = service_name
        self.username = username

    @property
    def supports_atomic_cas(self) -> bool:
        return False

    def load(self) -> tuple[dict | None, int]:
        try:
            raw = keyring.get_password(self.service_name, self.username)
        except Exception as exc:  # keyring backends raise a variety of things
            logger.error("Failed to read tokens from keyring: %s", exc)
            return None, 0
        if not raw:
            return None, 0
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Stored Jobber token is not valid JSON; treating as absent")
            return None, 0
        version = int(data.pop(self.VERSION_KEY, 0) or 0)
        return data, version

    def save(self, token_data: dict, *, expected_version: int) -> int | None:
        _, current = self.load()
        if current != expected_version:
            logger.info(
                "Jobber token changed underneath us (version %s -> %s); not overwriting",
                expected_version,
                current,
            )
            return CONFLICT
        payload = dict(token_data)
        payload[self.VERSION_KEY] = expected_version + 1
        try:
            keyring.set_password(self.service_name, self.username, json.dumps(payload))
        except Exception as exc:
            logger.error("Failed to store tokens in keyring: %s", exc)
            return CONFLICT
        return expected_version + 1

    def clear(self) -> bool:
        try:
            keyring.delete_password(self.service_name, self.username)
            return True
        except keyring.errors.PasswordDeleteError:
            return False
        except Exception as exc:
            logger.error("Failed to clear tokens from keyring: %s", exc)
            return False


__all__ = ["CONFLICT", "KeyringTokenStore", "TokenStore"]

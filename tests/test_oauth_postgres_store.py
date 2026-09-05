"""PostgresOAuthConnectionStore against a REAL PostgreSQL — encryption, restart
durability, and the one failure-handling detail most worth getting wrong.

Same DSN resolution and production guard as test_durability_real_postgres.py
(duplicated here — see the comment below the imports for why). Skips when no
reachable PostgreSQL is configured. This is LOCAL_REAL_VALIDATED: real asyncpg, real migration 008,
real Fernet encryption — nothing here is a mock standing in for the database.

Every test cleans up the row it wrote. Unlike the task/memory durability
tests, `oauth_connections` is meant to hold a small, known set of real
provider rows forever — leaving synthetic `test-oauth-*` rows in a shared
development database indefinitely would be untidy in a way leaving a UUID-
named task is not.
"""

from __future__ import annotations

import os
import uuid

import pytest
from cryptography.fernet import Fernet

from app.core.config import settings
from app.integrations.oauth.postgres_store import PostgresOAuthConnectionStore
from app.persistence.database import AsyncpgDatabase

pytestmark = pytest.mark.asyncio

# Same resolution and guard as test_durability_real_postgres.py, duplicated
# rather than imported: `tests/` is not a package (no __init__.py), so
# cross-file imports between test modules are not a pattern this codebase
# uses. Keep both in sync if the resolution order there ever changes.
DSN = (
    os.environ.get("THYNACT_TEST_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql://agent_os:agent_os_dev@127.0.0.1:5432/agent_os"
)


class _ProductionDatabaseRefused(RuntimeError):
    """The resolved DSN points at a database stamped `production`."""


async def _refuse_production(db: AsyncpgDatabase) -> None:
    try:
        rows = await db.fetch("SELECT environment FROM deployment_environment")
    except Exception:  # noqa: BLE001 - unstamped or pre-migration database
        return
    if rows and rows[0]["environment"] == "production":
        raise _ProductionDatabaseRefused(
            "Refusing to run OAuth store tests against a database stamped "
            "'production'. Set THYNACT_TEST_DATABASE_URL to a development database."
        )


async def _postgres_available() -> bool:
    try:
        db = AsyncpgDatabase(DSN)
        try:
            await db.fetch("SELECT 1")
            await _refuse_production(db)
        finally:
            await db.close()
        return True
    except _ProductionDatabaseRefused:
        raise
    except Exception:  # noqa: BLE001 - any failure means "no PostgreSQL here"
        return False


@pytest.fixture
def encryption_key(monkeypatch):
    """A real, freshly generated Fernet key — not a placeholder string, so a
    bug that skipped actual encryption (e.g. storing plaintext and only
    pretending to encrypt it) would still be exercised realistically."""
    monkeypatch.setattr(settings, "credential_encryption_key", Fernet.generate_key().decode())


@pytest.fixture
async def store(encryption_key):
    if not await _postgres_available():
        pytest.skip(f"no reachable PostgreSQL at {DSN.rsplit('@', 1)[-1]}")
    db = AsyncpgDatabase(DSN)
    yield PostgresOAuthConnectionStore(db)
    await db.close()


def _provider_id() -> str:
    return f"test-oauth-{uuid.uuid4()}"


async def test_a_token_survives_a_pool_and_store_rebuild(encryption_key):
    """The actual durability claim: not "the store returns what I just set,"
    but "a second store built from a second pool reads the first one's write."
    """
    if not await _postgres_available():
        pytest.skip("no reachable PostgreSQL")

    provider = _provider_id()
    db = AsyncpgDatabase(DSN)
    try:
        await PostgresOAuthConnectionStore(db).record_success(
            provider, access_token="gho_real_token_value", token_type="bearer", scope="repo"
        )
    finally:
        await db.close()

    rebuilt_db = AsyncpgDatabase(DSN)
    try:
        record = await PostgresOAuthConnectionStore(rebuilt_db).get(provider)
        assert record.access_token == "gho_real_token_value"
        assert record.token_type == "bearer"
        assert record.scope == "repo"
        assert record.connected is True
    finally:
        await PostgresOAuthConnectionStore(rebuilt_db).disconnect(provider)
        await rebuilt_db.close()


async def test_the_access_token_is_actually_encrypted_in_the_column(store):
    """Not "a `bytes` column exists" — the plaintext token must not appear
    anywhere in what PostgreSQL itself stored. Reads the raw column with a
    second connection, bypassing the store's own decrypt path entirely, so a
    store bug that decrypts correctly while writing plaintext would still be
    caught.
    """
    provider = _provider_id()
    try:
        await store.record_success(
            provider, access_token="super-secret-real-value", token_type="bearer", scope=None
        )

        raw = await store.db.fetchrow(
            "SELECT access_token_encrypted FROM oauth_connections WHERE provider = $1", provider
        )
        assert raw is not None
        ciphertext = bytes(raw["access_token_encrypted"])
        assert b"super-secret-real-value" not in ciphertext

        record = await store.get(provider)
        assert record.access_token == "super-secret-real-value"
    finally:
        await store.disconnect(provider)


async def test_a_wrong_encryption_key_refuses_to_decrypt_rather_than_returning_garbage(
    monkeypatch,
):
    """The failure mode a stale/rotated key must produce: a clear refusal, not
    a token-shaped string that silently fails every real request against the
    provider.
    """
    if not await _postgres_available():
        pytest.skip("no reachable PostgreSQL")
    from app.integrations.credential_crypto import CredentialEncryptionUnavailable

    provider = _provider_id()
    monkeypatch.setattr(settings, "credential_encryption_key", Fernet.generate_key().decode())
    db = AsyncpgDatabase(DSN)
    try:
        write_store = PostgresOAuthConnectionStore(db)
        await write_store.record_success(provider, access_token="tok", token_type="bearer", scope=None)

        # A different key, as if the deployment's secret had rotated without
        # re-encrypting existing rows.
        monkeypatch.setattr(settings, "credential_encryption_key", Fernet.generate_key().decode())
        with pytest.raises(CredentialEncryptionUnavailable):
            await write_store.get(provider)
    finally:
        # Delete directly — `disconnect()` calls `get()`, which would raise
        # the same error under the wrong key.
        await db.execute("DELETE FROM oauth_connections WHERE provider = $1", provider)
        await db.close()


async def test_record_failure_does_not_clobber_a_working_token(store):
    """The one detail in the upsert that is easy to get backwards: a failed
    probe (say, a revocation check) must only ever touch `last_error` — never
    null out an access token that still works.
    """
    provider = _provider_id()
    try:
        await store.record_success(provider, access_token="still-good-token", token_type="bearer", scope="repo")
        await store.record_failure(provider, error="transient network blip")

        record = await store.get(provider)
        assert record.access_token == "still-good-token", "a failure wiped a working token"
        assert record.last_error == "transient network blip"
    finally:
        await store.disconnect(provider)


async def test_a_fresh_success_clears_a_previous_error(store):
    provider = _provider_id()
    try:
        await store.record_failure(provider, error="expired code")
        assert (await store.get(provider)).last_error == "expired code"

        await store.record_success(provider, access_token="fresh-token", token_type="bearer", scope=None)
        record = await store.get(provider)
        assert record.last_error is None
        assert record.access_token == "fresh-token"
    finally:
        await store.disconnect(provider)


async def test_disconnect_reports_whether_a_connection_existed_and_removes_it(store):
    provider = _provider_id()
    assert await store.disconnect(provider) is False, "nothing was connected yet"

    await store.record_success(provider, access_token="tok", token_type="bearer", scope=None)
    assert await store.disconnect(provider) is True

    record = await store.get(provider)
    assert record.connected is False


async def test_get_on_an_unknown_provider_returns_a_disconnected_record_not_an_error(store):
    record = await store.get(_provider_id())
    assert record.connected is False
    assert record.access_token is None

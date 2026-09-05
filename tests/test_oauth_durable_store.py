from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.integrations.oauth.crypto import OAuthTokenCipher
from app.integrations.oauth.store import OAuthConnectionStore


class FakeDatabase:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[tuple[str, tuple]] = []

    async def fetch(self, query: str, *args):
        self.calls.append((query, args))
        return self.rows

    async def execute(self, query: str, *args):
        self.calls.append((query, args))
        return "OK"


def test_token_cipher_is_authenticated_and_never_plaintext() -> None:
    cipher = OAuthTokenCipher(Fernet.generate_key().decode())
    ciphertext = cipher.encrypt("access-secret")

    assert ciphertext != "access-secret"
    assert cipher.decrypt(ciphertext) == "access-secret"
    with pytest.raises(RuntimeError, match="could not be decrypted"):
        cipher.decrypt(ciphertext[:-2] + "xx")


@pytest.mark.asyncio
async def test_durable_store_loads_decrypts_and_scopes_by_tenant() -> None:
    cipher = OAuthTokenCipher(Fernet.generate_key().decode())
    db = FakeDatabase(
        rows=[
            {
                "provider": "github",
                "access_token_ciphertext": cipher.encrypt("access-secret"),
                "refresh_token_ciphertext": cipher.encrypt("refresh-secret"),
                "token_type": "bearer",
                "scope": "repo",
                "connected_at": "2026-09-05T00:00:00+00:00",
                "last_error": None,
            }
        ]
    )
    store = OAuthConnectionStore(database=db, tenant_id="tenant-a", cipher=cipher)

    await store.initialize()

    record = store.get("github")
    assert record.access_token == "access-secret"
    assert record.refresh_token == "refresh-secret"
    assert db.calls[0][1] == ("tenant-a",)


@pytest.mark.asyncio
async def test_durable_store_persists_ciphertext_and_disconnects_tenant_scope() -> None:
    cipher = OAuthTokenCipher(Fernet.generate_key().decode())
    db = FakeDatabase()
    store = OAuthConnectionStore(database=db, tenant_id="tenant-b", cipher=cipher)
    store.record_success(
        "slack",
        access_token="access-secret",
        refresh_token="refresh-secret",
        token_type="bearer",
        scope="chat:write",
    )

    await store.persist("slack")
    insert_args = db.calls[0][1]
    assert insert_args[0:2] == ("tenant-b", "slack")
    assert "access-secret" not in insert_args[2]
    assert "refresh-secret" not in insert_args[3]

    await store.persist_disconnect("slack")
    assert db.calls[1][1] == ("tenant-b", "slack")

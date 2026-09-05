from __future__ import annotations

from app.integrations.credential_crypto import decrypt_secret, encrypt_secret
from app.integrations.oauth.models import OAuthConnectionRecord, utcnow
from app.integrations.oauth.store import OAuthConnectionStore
from app.persistence.database import Database


class PostgresOAuthConnectionStore(OAuthConnectionStore):
    """Persists OAuth connections in `oauth_connections` (migration 008), the
    access token encrypted at rest — see credential_crypto.py. Selected via
    AGENT_OS_OAUTH_BACKEND=postgres; see app/integrations/oauth/registry.py.

    Every write is a single upsert on the provider primary key, so
    `record_success` after `record_failure` (or vice versa) does not require a
    read first — the same "read your own writes without a race" property the
    in-memory dict gave for free.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get(self, provider: str) -> OAuthConnectionRecord:
        row = await self.db.fetchrow(
            "SELECT access_token_encrypted, token_type, scope, connected_at, last_error "
            "FROM oauth_connections WHERE provider = $1",
            provider,
        )
        if row is None:
            return OAuthConnectionRecord(provider=provider)
        encrypted = row["access_token_encrypted"]
        return OAuthConnectionRecord(
            provider=provider,
            access_token=decrypt_secret(bytes(encrypted)) if encrypted else None,
            token_type=row["token_type"],
            scope=row["scope"],
            connected_at=row["connected_at"].isoformat() if row["connected_at"] else None,
            last_error=row["last_error"],
        )

    async def record_success(
        self, provider: str, *, access_token: str, token_type: str | None, scope: str | None
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO oauth_connections
                (provider, access_token_encrypted, token_type, scope, connected_at, last_error, updated_at)
            VALUES ($1, $2, $3, $4, $5, NULL, NOW())
            ON CONFLICT (provider) DO UPDATE SET
                access_token_encrypted = EXCLUDED.access_token_encrypted,
                token_type = EXCLUDED.token_type,
                scope = EXCLUDED.scope,
                connected_at = EXCLUDED.connected_at,
                last_error = NULL,
                updated_at = NOW()
            """,
            provider,
            encrypt_secret(access_token),
            token_type,
            scope,
            utcnow(),
        )

    async def record_failure(self, provider: str, *, error: str) -> None:
        # A failure must not clobber an access token that already works — an
        # expired-refresh probe failing should not disconnect a still-good
        # connection. Only last_error moves; every other column keeps
        # whatever it already had (or NULL, on first insert).
        await self.db.execute(
            """
            INSERT INTO oauth_connections (provider, last_error, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (provider) DO UPDATE SET
                last_error = EXCLUDED.last_error,
                updated_at = NOW()
            """,
            provider,
            error,
        )

    async def disconnect(self, provider: str) -> bool:
        existing = await self.get(provider)
        existed = existing.connected
        await self.db.execute("DELETE FROM oauth_connections WHERE provider = $1", provider)
        return existed

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.integrations.oauth.crypto import OAuthTokenCipher
from app.integrations.oauth.models import OAuthConnectionRecord, OAuthStateRecord, utcnow
from app.persistence.database import Database

STATE_TTL = timedelta(minutes=10)


class OAuthStateStore:
    """Short-lived, single-use CSRF state tokens for the authorize/callback
    round trip. In-memory and process-local, like the rest of this
    codebase's integration telemetry (see status_store.py) — a lost state on
    restart just means the user retries "Authorize", not a security issue."""

    def __init__(self) -> None:
        self._states: dict[str, OAuthStateRecord] = {}

    def create(self, provider: str) -> str:
        self._expire_old()
        token = uuid4().hex
        self._states[token] = OAuthStateRecord(provider=provider, created_at=utcnow())
        return token

    def consume(self, state: str) -> str | None:
        """Validate and invalidate a state token in one step. Returns the
        provider it was issued for, or None if it's missing/expired/reused."""
        self._expire_old()
        record = self._states.pop(state, None)
        if record is None:
            return None
        return record.provider

    def _expire_old(self) -> None:
        cutoff = utcnow() - STATE_TTL
        expired = [token for token, record in self._states.items() if record.created_at < cutoff]
        for token in expired:
            self._states.pop(token, None)


class OAuthConnectionStore:
    """Tracks one deployment tenant's OAuth connections.

    The in-memory mode remains useful for local development/tests. When a
    database and cipher are configured, the cache is loaded at startup and
    every token mutation is written encrypted to PostgreSQL. The tenant id is
    part of every database key so a future multi-tenant auth layer cannot
    accidentally read another tenant's connection.
    """

    def __init__(
        self,
        *,
        database: Database | None = None,
        tenant_id: str = "operator",
        cipher: OAuthTokenCipher | None = None,
    ) -> None:
        self._connections: dict[str, OAuthConnectionRecord] = {}
        self._database = database
        self._tenant_id = tenant_id
        self._cipher = cipher

    def configure(
        self,
        *,
        database: Database,
        tenant_id: str,
        cipher: OAuthTokenCipher,
    ) -> None:
        tenant = tenant_id.strip()
        if not tenant:
            raise ValueError("OAuth tenant id must be non-empty")
        self._database = database
        self._tenant_id = tenant
        self._cipher = cipher

    async def initialize(self) -> None:
        if self._database is None:
            return
        if self._cipher is None:
            raise RuntimeError("OAuth token encryption is not configured")
        rows = await self._database.fetch(
            """
            SELECT provider, access_token_ciphertext, refresh_token_ciphertext,
                   token_type, scope, expires_at, connected_at, last_error
            FROM oauth_connections
            WHERE tenant_id = $1
            """,
            self._tenant_id,
        )
        self._connections.clear()
        for row in rows:
            self._connections[row["provider"]] = OAuthConnectionRecord(
                provider=row["provider"],
                access_token=self._cipher.decrypt(row["access_token_ciphertext"]),
                refresh_token=(
                    self._cipher.decrypt(row["refresh_token_ciphertext"])
                    if row.get("refresh_token_ciphertext")
                    else None
                ),
                token_type=row.get("token_type"),
                scope=row.get("scope"),
                expires_at=str(row["expires_at"]) if row.get("expires_at") else None,
                connected_at=str(row["connected_at"]) if row.get("connected_at") else None,
                last_error=row.get("last_error"),
            )

    def get(self, provider: str) -> OAuthConnectionRecord:
        return self._connections.setdefault(provider, OAuthConnectionRecord(provider=provider))

    def record_success(
        self,
        provider: str,
        *,
        access_token: str,
        token_type: str | None,
        scope: str | None,
        refresh_token: str | None = None,
        expires_in: float | None = None,
        expires_at: str | None = None,
    ) -> None:
        record = self.get(provider)
        record.access_token = access_token
        record.refresh_token = refresh_token
        record.token_type = token_type
        record.scope = scope
        if expires_at is not None:
            record.expires_at = expires_at
        elif expires_in is not None:
            try:
                record.expires_at = (utcnow() + timedelta(seconds=float(expires_in))).isoformat()
            except (TypeError, ValueError):
                record.expires_at = None
        else:
            record.expires_at = None
        record.connected_at = utcnow().isoformat()
        record.last_error = None

    def record_failure(self, provider: str, *, error: str) -> None:
        record = self.get(provider)
        record.last_error = error

    def disconnect(self, provider: str) -> bool:
        existed = provider in self._connections and self._connections[provider].connected
        self._connections.pop(provider, None)
        return existed

    async def persist(self, provider: str) -> None:
        if self._database is None:
            return
        if self._cipher is None:
            raise RuntimeError("OAuth token encryption is not configured")
        record = self.get(provider)
        if not record.access_token:
            await self.persist_disconnect(provider)
            return
        connected_at = (
            datetime.fromisoformat(record.connected_at)
            if record.connected_at
            else utcnow()
        )
        await self._database.execute(
            """
            INSERT INTO oauth_connections (
                tenant_id, provider, access_token_ciphertext, refresh_token_ciphertext,
                token_type, scope, expires_at, connected_at, last_error
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (tenant_id, provider) DO UPDATE SET
                access_token_ciphertext = EXCLUDED.access_token_ciphertext,
                refresh_token_ciphertext = EXCLUDED.refresh_token_ciphertext,
                token_type = EXCLUDED.token_type,
                scope = EXCLUDED.scope,
                expires_at = EXCLUDED.expires_at,
                connected_at = EXCLUDED.connected_at,
                last_error = EXCLUDED.last_error
            """,
            self._tenant_id,
            provider,
            self._cipher.encrypt(record.access_token),
            self._cipher.encrypt(record.refresh_token) if record.refresh_token else None,
            record.token_type,
            record.scope,
            datetime.fromisoformat(record.expires_at) if record.expires_at else None,
            connected_at,
            record.last_error,
        )

    async def persist_disconnect(self, provider: str) -> None:
        if self._database is None:
            return
        await self._database.execute(
            "DELETE FROM oauth_connections WHERE tenant_id = $1 AND provider = $2",
            self._tenant_id,
            provider,
        )

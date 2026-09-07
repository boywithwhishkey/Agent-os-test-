from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.tenant import get_current_tenant
from app.integrations.oauth.crypto import OAuthTokenCipher
from app.integrations.oauth.models import (
    OAuthConnectionRecord,
    OAuthStateClaim,
    OAuthStateRecord,
    utcnow,
)
from app.persistence.database import Database

STATE_TTL = timedelta(minutes=10)


class OAuthStateStore:
    """Short-lived, single-use CSRF state tokens for the authorize/callback
    round trip. Development uses a process-local fallback; durable deployments
    store only a digest in PostgreSQL. Every claim carries its owning tenant so
    a public callback cannot attach a token to the wrong account."""

    def __init__(self) -> None:
        self._states: dict[str, OAuthStateRecord] = {}
        self._database: Database | None = None
        self._tenant_id = "operator"

    def configure(self, *, database: Database, tenant_id: str) -> None:
        tenant = tenant_id.strip()
        if not tenant:
            raise ValueError("OAuth state tenant id must be non-empty")
        self._database = database
        self._tenant_id = tenant

    def create(self, provider: str) -> str:
        self._expire_old()
        token = uuid4().hex
        self._states[token] = OAuthStateRecord(
            provider=provider,
            created_at=utcnow(),
            tenant_id=self._effective_tenant(),
        )
        return token

    def consume(self, state: str) -> str | None:
        """Validate and invalidate a state token in one step. Returns the
        provider it was issued for, or None if it's missing/expired/reused."""
        record = self._consume_record(state)
        if record is None:
            return None
        return record.provider

    def consume_claim(self, state: str) -> OAuthStateClaim | None:
        record = self._consume_record(state)
        if record is None:
            return None
        return OAuthStateClaim(provider=record.provider, tenant_id=record.tenant_id)

    async def create_async(self, provider: str) -> str:
        """Create state in PostgreSQL when durable OAuth storage is enabled."""
        if self._database is None:
            return self.create(provider)
        token = uuid4().hex
        tenant_id = self._effective_tenant()
        await self._database.execute(
            "DELETE FROM oauth_states WHERE tenant_id = $1 AND created_at < NOW() - INTERVAL '10 minutes'",
            tenant_id,
        )
        await self._database.execute(
            """
            INSERT INTO oauth_states (tenant_id, state_hash, provider, created_at)
            VALUES ($1, $2, $3, $4)
            """,
            tenant_id,
            self._hash(token),
            provider,
            utcnow(),
        )
        return token

    async def consume_async(self, state: str) -> str | None:
        """Atomically consume one durable state token, with TTL enforcement."""
        claim = await self.consume_claim_async(state)
        return claim.provider if claim else None

    async def consume_claim_async(self, state: str) -> OAuthStateClaim | None:
        """Consume state and return the tenant-bound OAuth claim."""
        if self._database is None:
            return self.consume_claim(state)
        tenant_id = self._effective_tenant()
        row = await self._database.fetchrow(
            """
            DELETE FROM oauth_states
            WHERE state_hash = $1
              AND created_at >= NOW() - INTERVAL '10 minutes'
            RETURNING provider, tenant_id
            """,
            self._hash(state),
        )
        if not row:
            return None
        return OAuthStateClaim(
            provider=row["provider"],
            tenant_id=str(row.get("tenant_id") or tenant_id),
        )

    @staticmethod
    def _hash(state: str) -> str:
        return hashlib.sha256(state.encode("utf-8")).hexdigest()

    def _expire_old(self) -> None:
        cutoff = utcnow() - STATE_TTL
        expired = [token for token, record in self._states.items() if record.created_at < cutoff]
        for token in expired:
            self._states.pop(token, None)

    def _consume_record(self, state: str) -> OAuthStateRecord | None:
        self._expire_old()
        return self._states.pop(state, None)

    def _effective_tenant(self) -> str:
        return get_current_tenant(self._tenant_id)


class OAuthConnectionStore:
    """Tracks one deployment tenant's OAuth connections.

    The in-memory mode remains useful for local development/tests. When a
    database and cipher are configured, encrypted rows for all tenants are
    loaded at startup and every token mutation is written to PostgreSQL. The
    cache key is always ``(tenant, provider)`` and the active tenant comes from
    server-held API-key context, never from a request header.
    """

    def __init__(
        self,
        *,
        database: Database | None = None,
        tenant_id: str = "operator",
        cipher: OAuthTokenCipher | None = None,
    ) -> None:
        self._connections: dict[tuple[str, str], OAuthConnectionRecord] = {}
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
            SELECT tenant_id, provider, access_token_ciphertext, refresh_token_ciphertext,
                   token_type, scope, expires_at, connected_at, last_error
            FROM oauth_connections
            """
        )
        self._connections.clear()
        for row in rows:
            tenant_id = str(row.get("tenant_id") or self._tenant_id)
            self._connections[(tenant_id, row["provider"])] = OAuthConnectionRecord(
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
        key = (self._effective_tenant(), provider)
        return self._connections.setdefault(key, OAuthConnectionRecord(provider=provider))

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
        key = (self._effective_tenant(), provider)
        existed = key in self._connections and self._connections[key].connected
        self._connections.pop(key, None)
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
            self._effective_tenant(),
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
            self._effective_tenant(),
            provider,
        )

    def _effective_tenant(self) -> str:
        return get_current_tenant(self._tenant_id)

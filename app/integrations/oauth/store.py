from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from uuid import uuid4

from app.integrations.oauth.models import OAuthConnectionRecord, OAuthStateRecord, utcnow

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


class OAuthConnectionStore(ABC):
    """Tracks the current OAuth connection per provider.

    Async on every method — including the in-memory implementation, which
    does no real I/O — so that a Postgres-backed implementation (see
    postgres_store.py) is a drop-in without every one of this codebase's ~10
    call sites needing to know which one it got. Access tokens are never
    included in any API response; see `OAuthConnectionRecord.to_public()`.

    Scoped by provider only, with no tenant or principal argument anywhere in
    this interface. That is deliberate and pinned by
    tests/test_connector_tenancy.py: THYNACT has no tenant model, so there is
    one connection per provider for the whole deployment. Adding tenancy here
    without it existing everywhere else would be worse than not having it.
    """

    @abstractmethod
    async def get(self, provider: str) -> OAuthConnectionRecord:
        raise NotImplementedError

    @abstractmethod
    async def record_success(
        self, provider: str, *, access_token: str, token_type: str | None, scope: str | None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def record_failure(self, provider: str, *, error: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self, provider: str) -> bool:
        raise NotImplementedError


class InMemoryOAuthConnectionStore(OAuthConnectionStore):
    """The original implementation, renamed to sit alongside
    PostgresOAuthConnectionStore rather than being the only option with no
    name for what it is — same naming shape as InMemoryApprovalStore
    elsewhere in this codebase. Behavior is unchanged: process memory only,
    lost on restart."""

    def __init__(self) -> None:
        self._connections: dict[str, OAuthConnectionRecord] = {}

    async def get(self, provider: str) -> OAuthConnectionRecord:
        return self._connections.setdefault(provider, OAuthConnectionRecord(provider=provider))

    async def record_success(
        self, provider: str, *, access_token: str, token_type: str | None, scope: str | None
    ) -> None:
        record = await self.get(provider)
        record.access_token = access_token
        record.token_type = token_type
        record.scope = scope
        record.connected_at = utcnow().isoformat()
        record.last_error = None

    async def record_failure(self, provider: str, *, error: str) -> None:
        record = await self.get(provider)
        record.last_error = error

    async def disconnect(self, provider: str) -> bool:
        existed = provider in self._connections and self._connections[provider].connected
        self._connections.pop(provider, None)
        return existed

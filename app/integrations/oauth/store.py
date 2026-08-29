from __future__ import annotations

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


class OAuthConnectionStore:
    """Tracks the current OAuth connection per provider. Access tokens live
    only in process memory and are never included in any API response —
    see OAuthConnectionRecord.to_public()."""

    def __init__(self) -> None:
        self._connections: dict[str, OAuthConnectionRecord] = {}

    def get(self, provider: str) -> OAuthConnectionRecord:
        return self._connections.setdefault(provider, OAuthConnectionRecord(provider=provider))

    def record_success(self, provider: str, *, access_token: str, token_type: str | None, scope: str | None) -> None:
        record = self.get(provider)
        record.access_token = access_token
        record.token_type = token_type
        record.scope = scope
        record.connected_at = utcnow().isoformat()
        record.last_error = None

    def record_failure(self, provider: str, *, error: str) -> None:
        record = self.get(provider)
        record.last_error = error

    def disconnect(self, provider: str) -> bool:
        existed = provider in self._connections and self._connections[provider].connected
        self._connections.pop(provider, None)
        return existed

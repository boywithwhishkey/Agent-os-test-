from __future__ import annotations

from app.core.config import settings
from app.core.lifecycle import register_resource
from app.integrations.oauth.store import (
    InMemoryOAuthConnectionStore,
    OAuthConnectionStore,
    OAuthStateStore,
)


def build_oauth_connection_store() -> OAuthConnectionStore:
    backend = settings.oauth_backend.lower().strip()
    if backend == "memory":
        return InMemoryOAuthConnectionStore()
    if backend == "postgres":
        from app.integrations.oauth.postgres_store import PostgresOAuthConnectionStore
        from app.persistence.database import AsyncpgDatabase

        database = register_resource(AsyncpgDatabase.from_settings())
        return PostgresOAuthConnectionStore(database)
    raise RuntimeError(f"Unsupported oauth backend: {backend}")


# Shared singletons: the authorize/callback routes and every OAuth adapter's
# test_connection()/run_capability() must see the same state/connection data,
# so this lives in one place both import rather than each owning its own
# instance.
oauth_state_store = OAuthStateStore()
oauth_connection_store = build_oauth_connection_store()

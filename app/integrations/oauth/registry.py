from __future__ import annotations

from app.integrations.oauth.store import OAuthConnectionStore, OAuthStateStore

# Shared singletons: authorize/callback routes and adapters must see the same
# state/connection data, so this lives in one place both import rather than
# each owning its own instance. Both stores fall back to process-local memory
# for development; the application configures their PostgreSQL backends when
# durable OAuth storage is enabled.
oauth_state_store = OAuthStateStore()
oauth_connection_store = OAuthConnectionStore()

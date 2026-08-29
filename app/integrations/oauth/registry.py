from __future__ import annotations

from app.integrations.oauth.store import OAuthConnectionStore, OAuthStateStore

# Shared singletons: the authorize/callback routes and the GitHub adapter's
# test_connection() must see the same state/connection data, so this lives
# in one place both import rather than each owning its own instance.
oauth_state_store = OAuthStateStore()
oauth_connection_store = OAuthConnectionStore()

-- Persists OAuth connections (GitHub, GitLab, Slack, Notion) so a user's
-- authorized account survives a restart. Previously in-process memory only
-- (app/integrations/oauth/store.py's InMemoryOAuthConnectionStore) — durable
-- storage is opt-in via AGENT_OS_OAUTH_BACKEND=postgres; memory stays the
-- default everywhere this migration has not been run.
--
-- access_token_encrypted is ciphertext, never plaintext — see
-- app/integrations/credential_crypto.py. token_type/scope/timestamps are not
-- secret and are stored in the clear for readability and debugging.
--
-- Scoped by provider only, matching the in-memory store exactly. THYNACT has
-- no tenant/principal model yet (see tests/test_connector_tenancy.py, which
-- pins that as a deliberate characterization, not an oversight) — this table
-- must not quietly invent per-user scoping the rest of the system does not
-- have. One row per provider, deployment-wide, the same as today.
CREATE TABLE IF NOT EXISTS oauth_connections (
    provider TEXT PRIMARY KEY,
    access_token_encrypted BYTEA,
    token_type TEXT,
    scope TEXT,
    connected_at TIMESTAMPTZ,
    last_error TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

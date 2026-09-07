-- OAuth state is a short-lived CSRF credential. Store only a SHA-256 digest,
-- never the browser-facing bearer value itself. tenant_id keeps concurrent
-- deployments/tenants from consuming one another's state.
CREATE TABLE IF NOT EXISTS oauth_states (
    tenant_id TEXT NOT NULL,
    state_hash TEXT NOT NULL,
    provider TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, state_hash)
);

CREATE INDEX IF NOT EXISTS idx_oauth_states_expiry
    ON oauth_states(tenant_id, created_at);

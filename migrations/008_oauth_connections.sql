-- OAuth credentials are encrypted by the application before this table sees
-- them. The database stores ciphertext only; tenant_id is part of the key so
-- a deployment cannot accidentally read another tenant's connection.
CREATE TABLE IF NOT EXISTS oauth_connections (
    tenant_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    access_token_ciphertext TEXT NOT NULL,
    refresh_token_ciphertext TEXT NULL,
    token_type TEXT NULL,
    scope TEXT NULL,
    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_error TEXT NULL,
    PRIMARY KEY (tenant_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_oauth_connections_tenant
    ON oauth_connections(tenant_id);

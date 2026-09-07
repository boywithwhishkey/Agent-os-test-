-- Governance records must follow the same tenant boundary as OAuth and MCP.
-- Existing single-operator rows are intentionally assigned to the legacy
-- `operator` tenant; new requests select the tenant from server-held API keys.
ALTER TABLE tool_approvals
    ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'operator';

ALTER TABLE tool_audit_events
    ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'operator';

CREATE INDEX IF NOT EXISTS idx_tool_approvals_tenant
    ON tool_approvals(tenant_id, approval_id);

CREATE INDEX IF NOT EXISTS idx_tool_audit_events_tenant
    ON tool_audit_events(tenant_id, timestamp);

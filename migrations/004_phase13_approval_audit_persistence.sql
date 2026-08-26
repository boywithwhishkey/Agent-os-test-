CREATE TABLE IF NOT EXISTS tool_approvals (
    approval_id TEXT PRIMARY KEY,
    tool TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    reason TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    consumed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_tool_approvals_tool
    ON tool_approvals(tool);

CREATE TABLE IF NOT EXISTS tool_audit_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    tool TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    risk TEXT NOT NULL,
    approval_required BOOLEAN NOT NULL,
    error TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_tool_audit_events_tool
    ON tool_audit_events(tool);
CREATE INDEX IF NOT EXISTS idx_tool_audit_events_timestamp
    ON tool_audit_events(timestamp);

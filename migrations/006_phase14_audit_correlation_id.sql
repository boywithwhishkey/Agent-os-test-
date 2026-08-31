-- Adds the correlation id to tool audit events so a tool execution can be
-- traced back to the originating HTTP request (the X-Correlation-ID that
-- correlation_middleware already assigns and echoes on every response).
--
-- Forward-only: migrations 001-005 are already applied and must never be
-- edited. Nullable by design — events recorded before this migration, and any
-- execution triggered outside an HTTP request, legitimately have no id.
ALTER TABLE tool_audit_events
    ADD COLUMN IF NOT EXISTS correlation_id TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_tool_audit_events_correlation_id
    ON tool_audit_events(correlation_id);

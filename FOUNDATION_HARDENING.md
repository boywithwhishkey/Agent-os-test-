# Foundation Hardening Pass

This patch corrects known shortcuts before Phase 7.

## Corrected limitations

1. **No agent self-approval**
   - Removed `approved: bool` from `ToolCall`.
   - Write/high-risk tools require a separate trusted approval grant.
   - Approval grants are single-use.

2. **Safer file access**
   - Workspace root is configurable.
   - Path traversal remains blocked.
   - `.env`, `.ssh`, `.git` and common private-key files are blocked from read tools.
   - Read/write size limits are enforced.

3. **Auditable tool execution**
   - Tool executions create structured audit events.
   - Audit endpoint is available for development.

4. **Future-ready policy boundary**
   - Authorization logic lives in `ToolPolicy`, not in tool handlers.
   - This can later be replaced by RBAC/ABAC/authenticated approvals without changing tools.

## Still intentionally deferred

- Durable PostgreSQL persistence
- authenticated users/RBAC
- distributed queue/workers
- cryptographically signed approval grants
- production audit persistence
- pgvector semantic memory
- n8n integration

These are scheduled for upcoming phases rather than hidden as technical debt.

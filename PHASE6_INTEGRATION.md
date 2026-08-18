# Phase 6 — Controlled Tool Execution

Adds:

- tool registry
- risk classification (`read`, `write`, `high_risk`)
- human-approval gate for write/high-risk tools
- workspace-safe file reads
- sandboxed artifact writes
- structured execution results
- REST endpoints:
  - `GET /api/v1/tools`
  - `POST /api/v1/tools/execute`

Phase 6 intentionally does **not** expose arbitrary shell execution.

## Verify

```bash
pytest
```

Expected result after Phase 6: 15 passing tests.

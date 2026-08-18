# Phase 7 — Memory & Context

Adds a backend-independent memory contract.

## Memory scopes
- session
- task
- project
- decision
- agent_run

## API
- `POST /api/v1/memory`
- `POST /api/v1/memory/search`
- `POST /api/v1/memory/context`
- `GET /api/v1/memory/{id}`
- `DELETE /api/v1/memory/{id}`

## Architecture

Agent logic depends on `MemoryService`, not on a database implementation.

Phase 7 uses an in-memory store for fast contract validation. Upcoming persistence adapters can add:
- PostgreSQL
- pgvector semantic retrieval
- Redis cache
- retention/summarization
- hybrid keyword + vector search

without changing the agent-facing memory API.

## Verify
`pytest`

Expected after Phase 7: 21 passing tests.

# Phase 11 — Durable Production Core

Phase 11 replaces the "in-memory only" limitation with production-ready
persistence adapters while keeping memory mode available for fast tests.

## Adds

- PostgreSQL database abstraction using asyncpg
- PostgreSQL-backed Agent OS memory
- PostgreSQL-backed workflow run checkpoints
- PostgreSQL-backed integration runtime execution history
- persistent idempotency records
- pgvector extension + embedding column foundation
- Redis job queue adapter
- in-memory queue for tests/development
- PostgreSQL + pgvector + Redis development compose stack
- database migration script
- backend selection through environment variables

## Backend configuration

```env
DATABASE_URL=postgresql://agent_os:agent_os_dev@localhost:5432/agent_os
REDIS_URL=redis://localhost:6379/0

AGENT_OS_MEMORY_BACKEND=postgres_pgvector
AGENT_OS_WORKFLOW_BACKEND=postgres
AGENT_OS_RUNTIME_BACKEND=postgres
AGENT_OS_QUEUE_BACKEND=redis
```

Keep all backend values as `memory` when running unit tests without infrastructure.

## Install and test

```bash
unzip -o agent-os-phase11.zip
python scripts/apply_phase11.py
pip install -e ".[dev]"
pytest
```

Expected: 43 tests passing.

## Start durable infrastructure

```bash
docker compose -f infra/platform/compose.yml up -d
docker compose -f infra/platform/compose.yml ps
python scripts/migrate_phase11.py
```

Then switch the backend environment variables from `memory` to PostgreSQL/Redis.

## Important

Phase 11 creates the pgvector storage foundation, but semantic embedding
generation/search is intentionally separated into the next intelligence layer.
This keeps persistence deterministic and provider-neutral.

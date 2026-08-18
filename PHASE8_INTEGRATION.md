# Phase 8 — Workflow Engine

Future-ready workflow orchestration layer.

## Features
- validated DAG definitions
- dependency execution
- concurrent execution of ready steps
- conditional steps
- retries
- per-step timeouts
- checkpointed run state
- pause on approval
- resume API
- pluggable agent runner
- tool execution integration
- backend-independent run store

## API
- `POST /api/v1/workflows/run`
- `POST /api/v1/workflows/runs/{run_id}/resume`
- `GET /api/v1/workflows/runs/{run_id}`

## Future adapters
The engine is intentionally independent of:
- PostgreSQL persistence
- Redis/queue workers
- Celery/Arq/Temporal-like durable workers
- n8n external workflow adapters
- model provider selection

## Verify
`pytest`

Expected after Phase 8: 28 passing tests.

# Agent OS

Python-first foundation for the multi-agent Agent OS.

## Current milestone

This starter provides:

- FastAPI application
- Health endpoint
- Task intake API
- Structured agent/task contracts with Pydantic
- Environment-based configuration
- Initial automated tests
- Docker support

## Run in GitHub Codespaces

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open `/docs` for Swagger UI.

## Run tests

```bash
pytest
```

## Endpoints

- `GET /health`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`

This first version intentionally uses an in-memory task store. PostgreSQL will replace it in the next foundation step after the contracts are verified.

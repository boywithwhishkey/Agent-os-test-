from __future__ import annotations

from app.core.config import settings

_POSTGRES_BACKENDS = {"postgres", "postgres_pgvector"}


async def check_readiness() -> dict[str, str]:
    checks: dict[str, str] = {}

    # Durable persistence was explicitly required but is not actually
    # configured — surface it as a readiness failure rather than letting the
    # deployment serve traffic while silently losing every write on restart.
    if settings.require_durable_persistence and settings.ephemeral_subsystems:
        checks["persistence"] = "ephemeral"

    uses_postgres = (
        settings.memory_backend in _POSTGRES_BACKENDS
        or settings.workflow_backend == "postgres"
        or settings.runtime_backend == "postgres"
        or settings.task_backend == "postgres"
        or settings.tool_backend == "postgres"
        or settings.workflow_definition_backend == "postgres"
    )
    if uses_postgres:
        checks["database"] = await _check_database()

    if settings.queue_backend == "redis":
        checks["queue"] = await _check_redis()

    # Always report the persistence posture, even when nothing durable is
    # configured. Without this the checks dict is EMPTY for an all-in-memory
    # deployment, and `all(...)` over an empty dict is vacuously true — so
    # /ready answered `200 {"status":"ready","checks":{}}` for a service that
    # loses every task, workflow, approval and audit record on restart. It was
    # the most confident-looking lie in the system.
    checks.setdefault("persistence", settings.persistence_mode)

    return checks


async def _check_database() -> str:
    if not settings.database_url:
        return "unconfigured"
    try:
        from app.persistence.database import AsyncpgDatabase

        database = AsyncpgDatabase.from_settings()
        try:
            await database.fetch("SELECT 1")
        finally:
            await database.close()
        return "ok"
    except Exception:  # noqa: BLE001 - any backend failure means "not ready"
        return "unavailable"


async def _check_redis() -> str:
    if not settings.redis_url:
        return "unconfigured"
    try:
        from app.queue.redis_queue import RedisJobQueue

        queue = RedisJobQueue.from_settings()
        try:
            client = await queue._get_client()
            await client.ping()
        finally:
            await queue.close()
        return "ok"
    except Exception:  # noqa: BLE001 - any backend failure means "not ready"
        return "unavailable"

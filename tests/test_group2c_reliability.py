import asyncio

import pytest

from app.core.config import settings
from app.core.readiness import check_readiness
from app.integrations.base import IntegrationAdapter
from app.integrations.models import IntegrationRequest, IntegrationResult
from app.persistence.database import Database
from app.persistence.migrations import run_migrations
from app.queue.base import InMemoryJobQueue, QueueJob
from app.queue.worker import JobWorker
from app.runtime.circuit_breaker import CircuitBreaker
from app.runtime.models import ExecutionStatus, RuntimeRequest
from app.runtime.rate_limit import SlidingWindowRateLimiter
from app.runtime.registry import ConnectorRegistry
from app.runtime.service import IntegrationRuntime
from app.runtime.store import InMemoryExecutionStore


class SlowAdapter(IntegrationAdapter):
    def __init__(self):
        self.calls = 0

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        self.calls += 1
        await asyncio.sleep(0.05)
        return IntegrationResult(provider="n8n", workflow=request.workflow, success=True)


def make_runtime(adapter):
    registry = ConnectorRegistry()
    registry.register("n8n", adapter)
    return IntegrationRuntime(
        registry=registry,
        store=InMemoryExecutionStore(),
        circuit_breaker=CircuitBreaker(3, 60),
        rate_limiter=SlidingWindowRateLimiter(100, 60),
        backoff_base_seconds=0,
    )


@pytest.mark.asyncio
async def test_concurrent_requests_with_same_idempotency_key_execute_once():
    adapter = SlowAdapter()
    runtime = make_runtime(adapter)
    request = RuntimeRequest(provider="n8n", workflow="payment", idempotency_key="op-concurrent")

    first, second = await asyncio.gather(runtime.execute(request), runtime.execute(request))

    assert adapter.calls == 1
    assert first.id == second.id
    assert first.status == ExecutionStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_worker_retries_then_succeeds():
    queue = InMemoryJobQueue()
    await queue.enqueue(QueueJob(type="notify", payload={}))
    calls = []

    async def handler(job: QueueJob) -> None:
        calls.append(job.attempts)
        if job.attempts == 0:
            raise RuntimeError("transient failure")

    worker = JobWorker(queue, handler, max_retries=2, backoff_base_seconds=0)

    assert await worker.process_one() is True
    assert await worker.process_one() is True
    assert await worker.process_one() is False

    assert calls == [0, 1]
    dead_letter = await queue.dequeue(worker.dead_letter_queue)
    assert dead_letter is None


@pytest.mark.asyncio
async def test_worker_moves_exhausted_job_to_dead_letter():
    queue = InMemoryJobQueue()
    await queue.enqueue(QueueJob(type="notify", payload={}))

    async def always_fails(job: QueueJob) -> None:
        raise RuntimeError("permanent failure")

    worker = JobWorker(queue, always_fails, max_retries=1, backoff_base_seconds=0)

    assert await worker.process_one() is True
    assert await worker.process_one() is True
    assert await worker.process_one() is False

    dead_letter = await queue.dequeue(worker.dead_letter_queue)
    assert dead_letter is not None
    assert dead_letter.attempts == 2


@pytest.mark.asyncio
async def test_readiness_reports_ephemeral_persistence_for_in_memory_backends():
    """Default in-memory backends add no dependency checks, but MUST still
    report the persistence posture.

    This previously asserted `checks == {}`, which encoded the bug: /ready
    computed health with `all(...)` over that empty dict, which is vacuously
    true, so an all-in-memory deployment answered `200 {"status": "ready"}`
    while losing every write on restart.
    """
    checks = await check_readiness()

    assert checks == {"persistence": "ephemeral"}
    assert "database" not in checks
    assert "queue" not in checks


@pytest.mark.asyncio
async def test_readiness_reports_unavailable_database(monkeypatch):
    monkeypatch.setattr(settings, "memory_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "postgres://bad-host/db")

    import app.core.readiness as readiness_module

    async def fake_check_database():
        return "unavailable"

    monkeypatch.setattr(readiness_module, "_check_database", fake_check_database)

    checks = await check_readiness()

    assert checks["database"] == "unavailable"
    # The persistence posture is reported alongside dependency checks, never
    # instead of them.
    assert checks["persistence"] == "partial"


class FakeMigrationDatabase(Database):
    def __init__(self):
        self.applied: set[str] = set()
        self.executed: list[str] = []

    async def execute(self, query, *args):
        self.executed.append(query.strip())
        if "INSERT INTO schema_migrations" in query:
            self.applied.add(args[0])
        return "OK"

    async def fetchrow(self, query, *args):
        return None

    async def fetch(self, query, *args):
        if "FROM schema_migrations" in query:
            return [{"version": v} for v in self.applied]
        return []


@pytest.mark.asyncio
async def test_migrations_apply_once_and_are_tracked():
    db = FakeMigrationDatabase()

    first_run = await run_migrations(db)
    assert first_run == sorted(first_run)
    assert len(first_run) >= 1
    assert "SELECT pg_advisory_lock(hashtext($1))" in db.executed
    assert "SELECT pg_advisory_unlock(hashtext($1))" in db.executed

    second_run = await run_migrations(db)
    assert second_run == []

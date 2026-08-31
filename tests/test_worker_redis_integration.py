"""Worker + Redis integration against a REAL Redis instance.

These are integration tests, not unit tests: they skip when no reachable Redis
is configured, so CI and laptops without Redis stay green, while an environment
that has one (the Claude cloud bootstrap, or CI's redis service) actually
exercises enqueue/dequeue, retry, dead-lettering and namespace isolation.

Nothing here proves production worker health — only that the code paths work
against a real broker locally.
"""

import os

import pytest

from app.queue.base import QueueJob
from app.queue.redis_queue import RedisJobQueue
from app.queue.worker import JobWorker

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")


async def _redis_available(url: str) -> bool:
    try:
        queue = RedisJobQueue(url, "probe")
        client = await queue._get_client()
        await client.ping()
        await queue.close()
        return True
    except Exception:  # noqa: BLE001 - any failure means "no Redis here"
        return False


@pytest.fixture
async def redis_queue():
    if not await _redis_available(REDIS_URL):
        pytest.skip("no reachable Redis")
    queue = RedisJobQueue(REDIS_URL, "agent-os-test:development")
    client = await queue._get_client()
    await client.delete(queue._key("default"), queue._key("default:dead-letter"))
    yield queue
    await client.delete(queue._key("default"), queue._key("default:dead-letter"))
    await queue.close()


@pytest.mark.asyncio
async def test_enqueue_and_dequeue_round_trip(redis_queue):
    job = QueueJob(type="demo", payload={"value": 1}, correlation_id="corr-worker-1")
    await redis_queue.enqueue(job)

    received = await redis_queue.dequeue("default", timeout=2)
    assert received is not None
    assert received.id == job.id
    assert received.payload == {"value": 1}
    # Correlation must survive the broker round trip or a job cannot be traced
    # back to the request that created it.
    assert received.correlation_id == "corr-worker-1"


@pytest.mark.asyncio
async def test_worker_processes_a_job(redis_queue):
    handled: list[str] = []

    async def handler(job: QueueJob) -> None:
        handled.append(job.type)

    await redis_queue.enqueue(QueueJob(type="ok"))
    worker = JobWorker(redis_queue, handler, queue_name="default")

    assert await worker.process_one(timeout=2) is True
    assert handled == ["ok"]


@pytest.mark.asyncio
async def test_worker_returns_false_on_empty_queue(redis_queue):
    async def handler(job: QueueJob) -> None:  # pragma: no cover - never called
        raise AssertionError("handler should not run on an empty queue")

    worker = JobWorker(redis_queue, handler, queue_name="default")
    assert await worker.process_one(timeout=1) is False


@pytest.mark.asyncio
async def test_failing_job_is_retried_then_dead_lettered(redis_queue):
    attempts: list[int] = []

    async def always_fails(job: QueueJob) -> None:
        attempts.append(job.attempts)
        raise RuntimeError("boom")

    await redis_queue.enqueue(QueueJob(type="poison"))
    worker = JobWorker(
        redis_queue, always_fails, queue_name="default", max_retries=2, backoff_base_seconds=0.01
    )

    # Initial attempt plus two retries; the third failure dead-letters it.
    for _ in range(3):
        assert await worker.process_one(timeout=2) is True

    assert attempts == [0, 1, 2]
    assert await redis_queue.dequeue("default", timeout=1) is None

    dead = await redis_queue.dequeue("default:dead-letter", timeout=2)
    assert dead is not None and dead.type == "poison"


@pytest.mark.asyncio
async def test_environments_cannot_consume_each_other_s_jobs():
    """The isolation guarantee, proven against a real broker.

    Both queues use the same Redis instance and the same logical queue name;
    only the environment namespace differs. A staging worker must never pick up
    a production job.
    """
    if not await _redis_available(REDIS_URL):
        pytest.skip("no reachable Redis")

    production = RedisJobQueue(REDIS_URL, "agent-os-test:production")
    staging = RedisJobQueue(REDIS_URL, "agent-os-test:staging")
    try:
        prod_client = await production.enqueue(QueueJob(type="production-only"))
        assert prod_client

        # Staging, same Redis, same queue name — must see nothing.
        assert await staging.dequeue("default", timeout=1) is None

        # And production still has its own job.
        received = await production.dequeue("default", timeout=2)
        assert received is not None and received.type == "production-only"
    finally:
        for queue in (production, staging):
            client = await queue._get_client()
            await client.delete(queue._key("default"))
            await queue.close()

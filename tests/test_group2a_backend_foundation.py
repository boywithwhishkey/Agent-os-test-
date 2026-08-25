import pytest

from app.core import lifecycle
from app.core.config import settings
from app.memory.factory import build_memory_service
from app.memory.in_memory import InMemoryMemoryStore
from app.queue.base import InMemoryJobQueue
from app.queue.factory import build_job_queue


def test_memory_backend_defaults_to_in_memory_store():
    service = build_memory_service()

    assert isinstance(service.store, InMemoryMemoryStore)


def test_unsupported_memory_backend_raises(monkeypatch):
    monkeypatch.setattr(settings, "memory_backend", "not-a-backend")

    with pytest.raises(RuntimeError, match="Unsupported memory backend"):
        build_memory_service()


def test_queue_backend_defaults_to_in_memory():
    queue = build_job_queue()

    assert isinstance(queue, InMemoryJobQueue)


def test_unsupported_queue_backend_raises(monkeypatch):
    monkeypatch.setattr(settings, "queue_backend", "not-a-backend")

    with pytest.raises(RuntimeError, match="Unsupported queue backend"):
        build_job_queue()


def test_postgres_memory_backend_requires_database_url(monkeypatch):
    monkeypatch.setattr(settings, "memory_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "")

    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        build_memory_service()


def test_redis_queue_backend_requires_redis_url(monkeypatch):
    monkeypatch.setattr(settings, "queue_backend", "redis")
    monkeypatch.setattr(settings, "redis_url", "")

    with pytest.raises(RuntimeError, match="REDIS_URL is required"):
        build_job_queue()


@pytest.mark.asyncio
async def test_lifecycle_close_all_closes_registered_resources():
    closed = []

    class FakeResource:
        async def close(self):
            closed.append(True)

    lifecycle.register_resource(FakeResource())
    await lifecycle.close_all()

    assert closed == [True]

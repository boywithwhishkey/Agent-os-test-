import pytest

from app.core.config import settings
from app.models.task import Task, TaskCreate, TaskPriority
from app.persistence.database import Database
from app.persistence.postgres_stores import PostgresTaskStore
from app.services.task_factory import build_task_store
from app.services.task_service import TaskService
from app.services.task_store import InMemoryTaskStore


class FakeDatabase(Database):
    def __init__(self):
        self.executed = []
        self.rows = {}

    async def execute(self, query, *args):
        self.executed.append((query, args))
        return "OK"

    async def fetchrow(self, query, *args):
        self.executed.append((query, args))
        return self.rows.get(args[0]) if args else None

    async def fetch(self, query, *args):
        self.executed.append((query, args))
        return []


@pytest.mark.asyncio
async def test_in_memory_task_store_roundtrip():
    store = InMemoryTaskStore()
    task = Task(objective="Build feature", priority=TaskPriority.NORMAL)
    await store.save(task)
    loaded = await store.get(task.id)
    assert loaded.id == task.id
    assert loaded.objective == "Build feature"


@pytest.mark.asyncio
async def test_in_memory_task_store_unknown_id_returns_none():
    store = InMemoryTaskStore()
    assert await store.get("does-not-exist") is None


@pytest.mark.asyncio
async def test_task_service_create_and_get():
    service = TaskService(InMemoryTaskStore())
    task = await service.create(TaskCreate(objective="Ship durable tasks"))
    assert task.status.value == "pending"
    fetched = await service.get(task.id)
    assert fetched.id == task.id


@pytest.mark.asyncio
async def test_postgres_task_store_save_and_get():
    db = FakeDatabase()
    store = PostgresTaskStore(db)
    task = Task(objective="Persist to postgres", priority=TaskPriority.HIGH)
    await store.save(task)
    assert "INSERT INTO tasks" in db.executed[0][0]

    db.rows[task.id] = {"payload": task.model_dump(mode="json")}
    loaded = await store.get(task.id)
    assert loaded.id == task.id
    assert loaded.priority == TaskPriority.HIGH


@pytest.mark.asyncio
async def test_postgres_task_store_unknown_id_returns_none():
    db = FakeDatabase()
    store = PostgresTaskStore(db)
    assert await store.get("missing") is None


def test_task_backend_defaults_to_in_memory_store():
    assert isinstance(build_task_store(), InMemoryTaskStore)


def test_unsupported_task_backend_raises(monkeypatch):
    monkeypatch.setattr(settings, "task_backend", "not-a-backend")
    with pytest.raises(RuntimeError, match="Unsupported task backend"):
        build_task_store()


def test_postgres_task_backend_requires_database_url(monkeypatch):
    monkeypatch.setattr(settings, "task_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        build_task_store()

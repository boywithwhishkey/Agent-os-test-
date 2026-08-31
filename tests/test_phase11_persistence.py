from datetime import UTC, datetime

import pytest

from app.memory.models import MemoryQuery, MemoryScope, MemoryWrite
from app.persistence.database import Database
from app.persistence.postgres_stores import (
    PostgresExecutionStore,
    PostgresMemoryStore,
    PostgresWorkflowRunStore,
)
from app.queue.base import InMemoryJobQueue, QueueJob
from app.runtime.models import ExecutionStatus, RuntimeExecution
from app.workflows.models import WorkflowRun, WorkflowStatus


class FakeDatabase(Database):
    def __init__(self):
        self.executed = []
        self.rows = {}
        self.lists = []

    async def execute(self, query, *args):
        self.executed.append((query, args))
        if query.strip().upper().startswith("DELETE"):
            return "DELETE 1"
        return "OK"

    async def fetchrow(self, query, *args):
        self.executed.append((query, args))
        return self.rows.get(args[0]) if args else None

    async def fetch(self, query, *args):
        self.executed.append((query, args))
        return list(self.lists)


@pytest.mark.asyncio
async def test_postgres_memory_write():
    db = FakeDatabase()
    store = PostgresMemoryStore(db)
    record = await store.write(
        MemoryWrite(scope=MemoryScope.PROJECT, key="architecture", content="Use durable stores")
    )
    assert record.key == "architecture"
    assert "INSERT INTO agent_memories" in db.executed[0][0]


@pytest.mark.asyncio
async def test_postgres_memory_get_and_search():
    now = datetime.now(UTC)
    row = {
        "id": "m1",
        "scope": "project",
        "key": "decision",
        "content": "postgres",
        "project_id": "p1",
        "task_id": None,
        "session_id": None,
        "agent": None,
        "tags": ["db"],
        "metadata": {"source": "test"},
        "importance": 0.8,
        "created_at": now,
    }
    db = FakeDatabase()
    db.rows["m1"] = row
    db.lists = [row]
    store = PostgresMemoryStore(db)
    assert (await store.get("m1")).content == "postgres"
    found = await store.search(MemoryQuery(project_id="p1", query="postgres"))
    assert found[0].id == "m1"


@pytest.mark.asyncio
async def test_postgres_workflow_roundtrip_shape():
    db = FakeDatabase()
    run = WorkflowRun(workflow_id="wf-1", status=WorkflowStatus.RUNNING)
    store = PostgresWorkflowRunStore(db)
    await store.save(run)
    db.rows[run.id] = {"payload": run.model_dump(mode="json")}
    loaded = await store.get(run.id)
    assert loaded.id == run.id
    assert loaded.status == WorkflowStatus.RUNNING


@pytest.mark.asyncio
async def test_postgres_runtime_idempotency_lookup():
    db = FakeDatabase()
    execution = RuntimeExecution(
        provider="n8n",
        workflow="notify",
        status=ExecutionStatus.SUCCEEDED,
        idempotency_key="idem-1",
        data={"ok": True},
    )
    store = PostgresExecutionStore(db)
    await store.save(execution)
    db.rows["idem-1"] = {"payload": execution.model_dump(mode="json")}
    loaded = await store.by_idempotency_key("idem-1")
    assert loaded.id == execution.id
    assert loaded.data == {"ok": True}


@pytest.mark.asyncio
async def test_in_memory_queue_fifo():
    queue = InMemoryJobQueue()
    first = QueueJob(type="workflow", payload={"n": 1})
    second = QueueJob(type="workflow", payload={"n": 2})
    await queue.enqueue(first)
    await queue.enqueue(second)
    assert (await queue.dequeue()).payload["n"] == 1
    assert (await queue.dequeue()).payload["n"] == 2


@pytest.mark.asyncio
async def test_memory_delete_reports_success():
    db = FakeDatabase()
    store = PostgresMemoryStore(db)
    assert await store.delete("m1") is True

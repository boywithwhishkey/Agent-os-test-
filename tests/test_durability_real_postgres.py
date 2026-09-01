"""Restart durability against a REAL PostgreSQL, and the environment stamp.

Every other "persistence" test in this suite writes through a FakeDatabase, so
they prove the SQL is issued, not that anything survives. These write through
real asyncpg, destroy the connection pool and every store object, rebuild from
scratch, and read the data back — the closest in-process analogue of the API
restarting.

Skips when no reachable PostgreSQL is configured, so laptops and CI without one
stay green.

This is LOCAL_REAL_VALIDATED. It says nothing about Render: production still
has no DATABASE_URL, and nothing here has been run against it.
"""

from __future__ import annotations

import os
import uuid

import pytest

from app.models.task import Task, TaskPriority
from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import (
    PostgresMemoryStore,
    PostgresTaskStore,
    PostgresToolAuditLog,
)

DSN = os.environ.get(
    "THYNACT_TEST_DATABASE_URL",
    "postgresql://agent_os:devlocal@localhost:5432/thynact_fresh",
)


async def _postgres_available() -> bool:
    try:
        db = AsyncpgDatabase(DSN)
        try:
            await db.fetch("SELECT 1")
        finally:
            await db.close()
        return True
    except Exception:  # noqa: BLE001 - any failure means "no PostgreSQL here"
        return False


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def fresh_db():
    if not await _postgres_available():
        pytest.skip(f"no reachable PostgreSQL at {DSN.rsplit('@', 1)[-1]}")
    db = AsyncpgDatabase(DSN)
    yield db
    await db.close()


async def test_task_survives_a_pool_and_store_rebuild():
    if not await _postgres_available():
        pytest.skip("no reachable PostgreSQL")

    task = Task(objective=f"durability-{uuid.uuid4()}", priority=TaskPriority.NORMAL)

    # --- "before the restart" -------------------------------------------
    db = AsyncpgDatabase(DSN)
    await PostgresTaskStore(db).save(task)
    # Tear down everything that held state: the pool, its connections, and the
    # store object itself. What remains lives only in PostgreSQL.
    await db.close()
    del db

    # --- "after the restart" --------------------------------------------
    rebuilt_db = AsyncpgDatabase(DSN)
    try:
        loaded = await PostgresTaskStore(rebuilt_db).get(task.id)
    finally:
        await rebuilt_db.close()

    assert loaded is not None, "task did not survive the rebuild"
    assert loaded.id == task.id
    assert loaded.objective == task.objective


async def test_audit_event_survives_a_pool_and_store_rebuild():
    if not await _postgres_available():
        pytest.skip("no reachable PostgreSQL")

    tool = f"durability-tool-{uuid.uuid4()}"
    correlation_id = str(uuid.uuid4())

    db = AsyncpgDatabase(DSN)
    await PostgresToolAuditLog(db).record(
        tool=tool,
        success=True,
        risk="read",
        approval_required=False,
        correlation_id=correlation_id,
    )
    await db.close()
    del db

    rebuilt_db = AsyncpgDatabase(DSN)
    try:
        events = await PostgresToolAuditLog(rebuilt_db).list()
    finally:
        await rebuilt_db.close()

    match = [e for e in events if e["tool"] == tool]
    assert match, "audit event did not survive the rebuild"
    # The correlation id is what makes an action traceable back to the request
    # that caused it, so it must survive too — not just the row.
    assert match[0]["correlation_id"] == correlation_id


async def test_memory_survives_a_pool_and_store_rebuild():
    if not await _postgres_available():
        pytest.skip("no reachable PostgreSQL")

    from app.memory.models import MemoryQuery, MemoryScope, MemoryWrite

    content = f"durability-memory-{uuid.uuid4()}"

    db = AsyncpgDatabase(DSN)
    written = await PostgresMemoryStore(db).write(
        MemoryWrite(scope=MemoryScope.PROJECT, key=f"durability-{uuid.uuid4()}", content=content)
    )
    await db.close()
    del db

    rebuilt_db = AsyncpgDatabase(DSN)
    try:
        results = await PostgresMemoryStore(rebuilt_db).search(
            MemoryQuery(query=content, limit=5)
        )
    finally:
        await rebuilt_db.close()

    assert any(r.id == written.id for r in results), (
        "memory did not survive the rebuild, or its embedding was not persisted"
    )


async def test_database_carries_an_environment_stamp(fresh_db):
    """Migration 007 stamps the database so an app can refuse a database
    belonging to a different environment."""
    rows = await fresh_db.fetch("SELECT environment FROM deployment_environment")

    assert rows, "deployment_environment is empty; migration 007 did not run"
    assert rows[0]["environment"] in {"production", "staging", "development", "test"}


async def test_environment_mismatch_is_refused(fresh_db):
    """The guard that stops a production deployment from opening the staging
    database (and vice versa)."""
    from app.persistence.environment import EnvironmentMismatchError, ensure_environment

    stamped = (await fresh_db.fetch("SELECT environment FROM deployment_environment"))[0][
        "environment"
    ]
    other = "production" if stamped != "production" else "staging"

    # Matching environment is allowed.
    await ensure_environment(fresh_db, stamped)

    # A different one is refused rather than silently sharing the database.
    with pytest.raises(EnvironmentMismatchError):
        await ensure_environment(fresh_db, other)

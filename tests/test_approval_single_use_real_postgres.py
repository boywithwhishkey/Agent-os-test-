"""Approval single-use semantics against a REAL PostgreSQL, including real concurrency.

`tests/test_approval_audit_persistence.py::test_postgres_approval_store_is_single_use`
already proves the query shape against a `FakeApprovalDatabase` — a Python dict
with sequential `await`s. That proves the SQL text is correct; it cannot prove
the UPDATE...WHERE consumed_at IS NULL...RETURNING clause actually stops two
concurrent consumers from both winning, because the fake has no row locking or
transaction isolation to get wrong. This file exercises the real
`PostgresApprovalStore` against real asyncpg connections, including firing two
`consume()` calls at the same approval_id truly concurrently (`asyncio.gather`
over two separate pooled connections), to prove Postgres's row-level locking is
what actually enforces single-use, not just the store's Python-level logic.

Follows the same DSN/skip/production-refusal pattern as
`test_durability_real_postgres.py` — see that file for why the fallback DSN and
`_refuse_production` guard are safe defaults rather than an accidental way to
run against production.
"""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest

from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import PostgresApprovalStore

DSN = (
    os.environ.get("THYNACT_TEST_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql://agent_os:agent_os_dev@127.0.0.1:5432/agent_os"
)


class ProductionDatabaseRefused(RuntimeError):
    """The resolved DSN points at a database stamped `production`."""


async def _refuse_production(db: AsyncpgDatabase) -> None:
    try:
        rows = await db.fetch("SELECT environment FROM deployment_environment")
    except Exception:  # noqa: BLE001 - unstamped or pre-migration database
        return
    if rows and rows[0]["environment"] == "production":
        raise ProductionDatabaseRefused(
            "Refusing to run approval durability tests against a database stamped "
            "'production'. Set THYNACT_TEST_DATABASE_URL to a development database."
        )


async def _postgres_available() -> bool:
    try:
        db = AsyncpgDatabase(DSN)
        try:
            await db.fetch("SELECT 1")
            await _refuse_production(db)
        finally:
            await db.close()
        return True
    except ProductionDatabaseRefused:
        raise
    except Exception:  # noqa: BLE001 - any failure means "no PostgreSQL here"
        return False


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db():
    if not await _postgres_available():
        pytest.skip(f"no reachable PostgreSQL at {DSN.rsplit('@', 1)[-1]}")
    database = AsyncpgDatabase(DSN)
    yield database
    await database.close()


async def test_approval_is_single_use_against_real_postgres(db):
    store = PostgresApprovalStore(db)
    tool = f"durability-tool-{uuid.uuid4()}"
    grant = await store.issue(tool, approved_by="tester", reason="single-use check")

    first = await store.consume(grant.approval_id, tool)
    second = await store.consume(grant.approval_id, tool)

    assert first is not None
    assert first.approval_id == grant.approval_id
    assert second is None, "a second sequential consume must not re-grant the approval"


async def test_concurrent_double_consume_cannot_both_succeed(db):
    """The real proof: fire two consume() calls at the same approval truly
    concurrently, over two separate pooled connections. Real row-level locking
    on the UPDATE means the second transaction blocks until the first commits,
    then re-evaluates `consumed_at IS NULL` against the now-updated row and
    finds no match — so exactly one of the two racing calls may return a
    grant, never both and never zero.
    """
    store = PostgresApprovalStore(db)
    tool = f"durability-tool-{uuid.uuid4()}"
    grant = await store.issue(tool, approved_by="tester", reason="concurrency check")

    results = await asyncio.gather(
        store.consume(grant.approval_id, tool),
        store.consume(grant.approval_id, tool),
    )

    successes = [r for r in results if r is not None]
    assert len(successes) == 1, (
        f"exactly one concurrent consume() must win the approval, got {len(successes)}"
    )
    assert successes[0].approval_id == grant.approval_id

    # And a third, strictly-after consume still finds it already spent.
    third = await store.consume(grant.approval_id, tool)
    assert third is None


async def test_many_concurrent_consumers_only_one_wins(db):
    """Same proof with higher contention (10-way race) to make it very unlikely
    that a subtle non-atomic path (e.g. read-then-write instead of a single
    UPDATE...RETURNING) would slip through by luck.
    """
    store = PostgresApprovalStore(db)
    tool = f"durability-tool-{uuid.uuid4()}"
    grant = await store.issue(tool, approved_by="tester", reason="high-contention check")

    results = await asyncio.gather(
        *[store.consume(grant.approval_id, tool) for _ in range(10)]
    )

    successes = [r for r in results if r is not None]
    assert len(successes) == 1, (
        f"exactly one of 10 concurrent consumers must win, got {len(successes)}"
    )

from datetime import UTC, datetime

import pytest

from app.core.config import settings
from app.persistence.database import Database
from app.persistence.postgres_stores import PostgresApprovalStore, PostgresToolAuditLog
from app.tools.approvals import InMemoryApprovalStore
from app.tools.audit import InMemoryToolAuditLog
from app.tools.factory import build_approval_store, build_tool_audit_log


class FakeApprovalDatabase(Database):
    def __init__(self):
        self._rows = {}

    async def execute(self, query, *args):
        return "OK"

    async def fetchrow(self, query, *args):
        if query.strip().upper().startswith("INSERT INTO TOOL_APPROVALS"):
            approval_id, tool, approved_by, reason = args
            self._rows[approval_id] = {
                "approval_id": approval_id,
                "tool": tool,
                "approved_by": approved_by,
                "reason": reason,
                "consumed": False,
            }
            return dict(self._rows[approval_id])
        if query.strip().upper().startswith("UPDATE TOOL_APPROVALS"):
            approval_id, tool = args
            record = self._rows.get(approval_id)
            if not record or record["tool"] != tool or record["consumed"]:
                return None
            record["consumed"] = True
            return {
                "approval_id": record["approval_id"],
                "tool": record["tool"],
                "approved_by": record["approved_by"],
                "reason": record["reason"],
            }
        return None

    async def fetch(self, query, *args):
        return []


class FakeAuditDatabase(Database):
    def __init__(self):
        self.inserted = []

    async def execute(self, query, *args):
        self.inserted.append(args)
        return "OK"

    async def fetchrow(self, query, *args):
        return None

    async def fetch(self, query, *args):
        now = datetime.now(UTC)
        return [
            {
                "timestamp": now,
                "tool": tool,
                "success": success,
                "risk": risk,
                "approval_required": approval_required,
                "error": error,
            }
            for (tool, success, risk, approval_required, error) in self.inserted
        ]


@pytest.mark.asyncio
async def test_in_memory_approval_is_single_use():
    store = InMemoryApprovalStore()
    grant = await store.issue("artifact.write", approved_by="tester")
    first = await store.consume(grant.approval_id, "artifact.write")
    second = await store.consume(grant.approval_id, "artifact.write")
    assert first is not None
    assert second is None


@pytest.mark.asyncio
async def test_in_memory_audit_log_records_events():
    log = InMemoryToolAuditLog()
    await log.record(tool="echo", success=True, risk="read", approval_required=False)
    events = await log.list()
    assert len(events) == 1
    assert events[0]["tool"] == "echo"


@pytest.mark.asyncio
async def test_postgres_approval_store_is_single_use():
    db = FakeApprovalDatabase()
    store = PostgresApprovalStore(db)
    grant = await store.issue("artifact.write", approved_by="tester", reason="test")
    first = await store.consume(grant.approval_id, "artifact.write")
    second = await store.consume(grant.approval_id, "artifact.write")
    assert first is not None
    assert first.tool == "artifact.write"
    assert second is None


@pytest.mark.asyncio
async def test_postgres_approval_store_wrong_tool_rejected():
    db = FakeApprovalDatabase()
    store = PostgresApprovalStore(db)
    grant = await store.issue("artifact.write", approved_by="tester")
    result = await store.consume(grant.approval_id, "other.tool")
    assert result is None


@pytest.mark.asyncio
async def test_postgres_audit_log_records_and_lists():
    db = FakeAuditDatabase()
    log = PostgresToolAuditLog(db)
    await log.record(tool="echo", success=True, risk="read", approval_required=False)
    events = await log.list()
    assert len(events) == 1
    assert events[0]["tool"] == "echo"
    assert isinstance(events[0]["timestamp"], str)


def test_tool_backend_defaults_to_in_memory():
    assert isinstance(build_approval_store(), InMemoryApprovalStore)
    assert isinstance(build_tool_audit_log(), InMemoryToolAuditLog)


def test_unsupported_tool_backend_raises(monkeypatch):
    monkeypatch.setattr(settings, "tool_backend", "not-a-backend")
    with pytest.raises(RuntimeError, match="Unsupported tool backend"):
        build_approval_store()
    with pytest.raises(RuntimeError, match="Unsupported tool backend"):
        build_tool_audit_log()


def test_postgres_tool_backend_requires_database_url(monkeypatch):
    monkeypatch.setattr(settings, "tool_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        build_approval_store()

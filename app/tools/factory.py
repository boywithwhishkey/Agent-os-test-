from __future__ import annotations

from app.core.config import settings
from app.core.lifecycle import register_resource
from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import PostgresApprovalStore, PostgresToolAuditLog
from app.tools.approvals import ApprovalStore, InMemoryApprovalStore
from app.tools.audit import InMemoryToolAuditLog, ToolAuditLog


def build_approval_store() -> ApprovalStore:
    backend = settings.tool_backend.lower().strip()
    if backend == "memory":
        return InMemoryApprovalStore()
    if backend == "postgres":
        database = register_resource(AsyncpgDatabase.from_settings())
        return PostgresApprovalStore(database)
    raise RuntimeError(f"Unsupported tool backend: {backend}")


def build_tool_audit_log() -> ToolAuditLog:
    backend = settings.tool_backend.lower().strip()
    if backend == "memory":
        return InMemoryToolAuditLog()
    if backend == "postgres":
        database = register_resource(AsyncpgDatabase.from_settings())
        return PostgresToolAuditLog(database)
    raise RuntimeError(f"Unsupported tool backend: {backend}")

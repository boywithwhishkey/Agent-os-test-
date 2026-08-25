from __future__ import annotations

from app.core.config import settings
from app.core.lifecycle import register_resource
from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import PostgresWorkflowRunStore
from app.tools.approvals import ApprovalStore
from app.tools.audit import InMemoryToolAuditLog
from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.policy import ToolPolicy
from app.workflows.engine import WorkflowEngine
from app.workflows.store import InMemoryWorkflowRunStore, WorkflowRunStore


async def default_agent_runner(payload: dict):
    return {
        "status": "agent_adapter_placeholder",
        "payload": payload,
    }


def build_workflow_run_store() -> WorkflowRunStore:
    backend = settings.workflow_backend.lower().strip()
    if backend == "memory":
        return InMemoryWorkflowRunStore()
    if backend == "postgres":
        database = register_resource(AsyncpgDatabase.from_settings())
        return PostgresWorkflowRunStore(database)
    raise RuntimeError(f"Unsupported workflow backend: {backend}")


def build_workflow_engine() -> WorkflowEngine:
    approvals = ApprovalStore()
    audit = InMemoryToolAuditLog()
    executor = ToolExecutor(
        build_default_registry(),
        ToolPolicy(approvals),
        audit,
    )
    return WorkflowEngine(
        store=build_workflow_run_store(),
        tool_executor=executor,
        agent_runner=default_agent_runner,
    )

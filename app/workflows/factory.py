from __future__ import annotations

from app.core.config import settings
from app.core.lifecycle import register_resource
from app.llm.factory import build_llm_provider
from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import (
    PostgresWorkflowDefinitionStore,
    PostgresWorkflowRunStore,
)
from app.runtime.factory import build_connector_registry
from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.factory import build_approval_store, build_tool_audit_log
from app.tools.policy import ToolPolicy
from app.workflows.definition_store import (
    InMemoryWorkflowDefinitionStore,
    WorkflowDefinitionStore,
)
from app.workflows.engine import WorkflowEngine
from app.workflows.handlers import build_llm_agent_runner
from app.workflows.store import InMemoryWorkflowRunStore, WorkflowRunStore


def build_workflow_run_store() -> WorkflowRunStore:
    backend = settings.workflow_backend.lower().strip()
    if backend == "memory":
        return InMemoryWorkflowRunStore()
    if backend == "postgres":
        database = register_resource(AsyncpgDatabase.from_settings())
        return PostgresWorkflowRunStore(database)
    raise RuntimeError(f"Unsupported workflow backend: {backend}")


def build_workflow_definition_store() -> WorkflowDefinitionStore:
    backend = settings.workflow_definition_backend.lower().strip()
    if backend == "memory":
        return InMemoryWorkflowDefinitionStore()
    if backend == "postgres":
        database = register_resource(AsyncpgDatabase.from_settings())
        return PostgresWorkflowDefinitionStore(database)
    raise RuntimeError(f"Unsupported workflow definition backend: {backend}")


def build_workflow_engine() -> WorkflowEngine:
    approvals = build_approval_store()
    audit = build_tool_audit_log()
    executor = ToolExecutor(
        build_default_registry(),
        ToolPolicy(approvals),
        audit,
    )
    return WorkflowEngine(
        store=build_workflow_run_store(),
        tool_executor=executor,
        agent_runner=build_llm_agent_runner(build_llm_provider()),
        connector_registry=build_connector_registry(),
    )

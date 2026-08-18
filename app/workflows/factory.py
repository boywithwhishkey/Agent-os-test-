from __future__ import annotations

from app.tools.approvals import ApprovalStore
from app.tools.audit import InMemoryToolAuditLog
from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.policy import ToolPolicy
from app.workflows.engine import WorkflowEngine
from app.workflows.store import InMemoryWorkflowRunStore


async def default_agent_runner(payload: dict):
    return {
        "status": "agent_adapter_placeholder",
        "payload": payload,
    }


def build_workflow_engine() -> WorkflowEngine:
    approvals = ApprovalStore()
    audit = InMemoryToolAuditLog()
    executor = ToolExecutor(
        build_default_registry(),
        ToolPolicy(approvals),
        audit,
    )
    return WorkflowEngine(
        store=InMemoryWorkflowRunStore(),
        tool_executor=executor,
        agent_runner=default_agent_runner,
    )

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.auth import require_api_key
from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.factory import build_approval_store, build_tool_audit_log
from app.tools.models import ApprovalGrant, ToolCall, ToolExecutionResult
from app.tools.policy import ToolPolicy

router = APIRouter(
    prefix="/api/v1/tools",
    tags=["tools"],
    dependencies=[Depends(require_api_key)],
)
registry = build_default_registry()
approvals = build_approval_store()
audit_log = build_tool_audit_log()
executor = ToolExecutor(registry, ToolPolicy(approvals), audit_log)


class ToolExecuteRequest(BaseModel):
    call: ToolCall
    approval_id: str | None = None


class ApprovalRequest(BaseModel):
    tool: str
    approved_by: str = Field(min_length=1)
    reason: str | None = None


@router.get("")
async def list_tools() -> list[dict[str, str]]:
    return [
        {"name": t.name, "description": t.description, "risk": t.risk.value}
        for t in registry.list_tools()
    ]


@router.post("/execute", response_model=ToolExecutionResult)
async def execute_tool(payload: ToolExecuteRequest) -> ToolExecutionResult:
    return await executor.execute(payload.call, approval_id=payload.approval_id)


@router.post("/approvals", response_model=ApprovalGrant)
async def create_approval(payload: ApprovalRequest) -> ApprovalGrant:
    # Temporary local approval service.
    # Authentication/authorization is added before production exposure.
    registry.get(payload.tool)
    return await approvals.issue(payload.tool, payload.approved_by, payload.reason)


@router.get("/audit")
async def get_tool_audit() -> list[dict]:
    return await audit_log.list()

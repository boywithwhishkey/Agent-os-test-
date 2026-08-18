from fastapi import APIRouter

from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.models import ToolCall, ToolExecutionResult

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])
registry = build_default_registry()
executor = ToolExecutor(registry)


@router.get("")
async def list_tools() -> list[dict[str, str]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "risk": tool.risk.value,
        }
        for tool in registry.list_tools()
    ]


@router.post("/execute", response_model=ToolExecutionResult)
async def execute_tool(call: ToolCall) -> ToolExecutionResult:
    return await executor.execute(call)

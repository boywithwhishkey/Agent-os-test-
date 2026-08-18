from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.tools.executor import ToolExecutor
from app.tools.models import ToolCall
from app.workflows.models import WorkflowStep

AgentRunner = Callable[[dict[str, Any]], Awaitable[Any]]


async def run_noop(step: WorkflowStep, context: dict[str, Any]) -> Any:
    return step.input.get("value")


async def run_tool(
    step: WorkflowStep,
    context: dict[str, Any],
    *,
    executor: ToolExecutor,
    approval_id: str | None = None,
) -> Any:
    tool = step.input.get("tool")
    arguments = step.input.get("arguments", {})
    if not isinstance(tool, str):
        raise ValueError("Tool step requires input.tool")
    result = await executor.execute(
        ToolCall(tool=tool, arguments=arguments),
        approval_id=approval_id,
    )
    if result.approval_required:
        return {"waiting_approval": True, "result": result.model_dump()}
    if not result.success:
        raise RuntimeError(result.error or "Tool execution failed")
    return result.output


async def run_agent(
    step: WorkflowStep,
    context: dict[str, Any],
    *,
    agent_runner: AgentRunner,
) -> Any:
    return await agent_runner(
        {
            "step_id": step.id,
            "input": step.input,
            "workflow_context": context,
        }
    )

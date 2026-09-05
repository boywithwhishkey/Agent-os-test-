from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.llm.base import LLMProvider, LLMRequest
from app.runtime.registry import ConnectorRegistry
from app.tools.executor import ToolExecutor
from app.tools.models import ToolCall
from app.workflows.integration_handler import run_integration_step
from app.workflows.models import WorkflowStep

AgentRunner = Callable[[dict[str, Any]], Awaitable[Any]]

DEFAULT_AGENT_SYSTEM_PROMPT = "You are a workflow specialist agent. Complete only the assigned task."


def build_llm_agent_runner(provider: LLMProvider) -> AgentRunner:
    """Provider-neutral AGENT step runner backed by any LLMProvider."""

    async def run(payload: dict[str, Any]) -> Any:
        step_input = payload.get("input", {})
        prompt = step_input.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Agent step requires input.prompt")
        system = step_input.get("system_prompt", DEFAULT_AGENT_SYSTEM_PROMPT)
        output = await provider.generate(LLMRequest(system=system, prompt=prompt))
        return {"output": output}

    return run


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
        raise ValueError("Tool step requires input.tool")  # noqa: TRY004 - step config validation
    result = await executor.execute(
        ToolCall(tool=tool, arguments=arguments),
        approval_id=approval_id,
        correlation_id=context.get("correlation_id"),
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


async def run_integration(
    step: WorkflowStep,
    context: dict[str, Any],
    *,
    connector_registry: ConnectorRegistry,
) -> Any:
    provider = step.input.get("provider")
    if not isinstance(provider, str):
        raise ValueError(  # noqa: TRY004 - step config validation
            "Integration step requires input.provider"
        )
    adapter = connector_registry.get(provider)
    return await run_integration_step(
        adapter=adapter,
        workflow=step.input.get("workflow", step.id),
        payload=step.input.get("payload", {}),
        correlation_id=context.get("correlation_id"),
        timeout_seconds=step.timeout_seconds,
    )

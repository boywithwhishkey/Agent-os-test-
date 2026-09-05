from __future__ import annotations

import asyncio
from typing import Any

from app.runtime.registry import ConnectorRegistry
from app.tools.executor import ToolExecutor
from app.workflows.handlers import AgentRunner, run_agent, run_integration, run_noop, run_tool
from app.workflows.models import (
    StepRun,
    StepStatus,
    StepType,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
)
from app.workflows.store import WorkflowRunStore


class WorkflowEngine:
    def __init__(
        self,
        *,
        store: WorkflowRunStore,
        tool_executor: ToolExecutor,
        agent_runner: AgentRunner,
        connector_registry: ConnectorRegistry | None = None,
        max_parallel: int = 8,
    ) -> None:
        self.store = store
        self.tool_executor = tool_executor
        self.agent_runner = agent_runner
        self.connector_registry = connector_registry or ConnectorRegistry()
        self.semaphore = asyncio.Semaphore(max_parallel)

    async def start(
        self,
        definition: WorkflowDefinition,
        context: dict[str, Any] | None = None,
        *,
        correlation_id: str | None = None,
    ) -> WorkflowRun:
        run_context = dict(context or {})
        resolved_correlation_id = correlation_id or run_context.get("correlation_id")
        if resolved_correlation_id is not None:
            run_context["correlation_id"] = resolved_correlation_id
        run = WorkflowRun(
            workflow_id=definition.id,
            correlation_id=resolved_correlation_id,
            status=WorkflowStatus.RUNNING,
            context=run_context,
            steps={
                step.id: StepRun(step_id=step.id)
                for step in definition.steps
            },
        )
        await self.store.save(run)
        return await self._drive(definition, run)

    async def resume(
        self,
        definition: WorkflowDefinition,
        run_id: str,
        *,
        approvals: dict[str, str] | None = None,
    ) -> WorkflowRun:
        run = await self.store.get(run_id)
        if run is None:
            raise KeyError(f"Unknown workflow run: {run_id}")

        if run.correlation_id is not None:
            run.context["correlation_id"] = run.correlation_id

        approvals = approvals or {}
        for step_id, approval_id in approvals.items():
            if step_id in run.steps:
                run.steps[step_id].approval_id = approval_id
                if run.steps[step_id].status == StepStatus.WAITING_APPROVAL:
                    run.steps[step_id].status = StepStatus.PENDING

        run.status = WorkflowStatus.RUNNING
        await self.store.save(run)
        return await self._drive(definition, run)

    def _condition_passes(
        self,
        step: WorkflowStep,
        run: WorkflowRun,
    ) -> bool:
        if step.condition_key is None:
            return True
        return run.context.get(step.condition_key) == step.condition_equals

    async def _execute_step(
        self,
        step: WorkflowStep,
        run: WorkflowRun,
    ) -> tuple[str, StepRun]:
        state = run.steps[step.id]
        state.status = StepStatus.RUNNING

        async with self.semaphore:
            for attempt in range(state.attempts + 1, step.max_retries + 2):
                state.attempts = attempt
                try:
                    async with asyncio.timeout(step.timeout_seconds):
                        if step.type == StepType.NOOP:
                            output = await run_noop(step, run.context)
                        elif step.type == StepType.TOOL:
                            output = await run_tool(
                                step,
                                run.context,
                                executor=self.tool_executor,
                                approval_id=state.approval_id,
                            )
                            if isinstance(output, dict) and output.get("waiting_approval"):
                                state.status = StepStatus.WAITING_APPROVAL
                                state.output = output["result"]
                                state.error = None
                                return step.id, state
                        elif step.type == StepType.AGENT:
                            output = await run_agent(
                                step,
                                run.context,
                                agent_runner=self.agent_runner,
                            )
                        elif step.type == StepType.INTEGRATION:
                            output = await run_integration(
                                step,
                                run.context,
                                connector_registry=self.connector_registry,
                            )
                        else:
                            raise ValueError(f"Unsupported step type: {step.type}")

                    state.output = output
                    state.error = None
                    state.status = StepStatus.COMPLETED
                    return step.id, state
                except Exception as exc:  # noqa: BLE001 - step failures become retryable state
                    state.error = f"{type(exc).__name__}: {exc}"
                    if attempt > step.max_retries:
                        state.status = StepStatus.FAILED
                        return step.id, state

        return step.id, state

    async def _drive(
        self,
        definition: WorkflowDefinition,
        run: WorkflowRun,
    ) -> WorkflowRun:
        while True:
            terminal = {
                StepStatus.COMPLETED,
                StepStatus.FAILED,
                StepStatus.SKIPPED,
            }
            if all(state.status in terminal for state in run.steps.values()):
                run.status = (
                    WorkflowStatus.FAILED
                    if any(s.status == StepStatus.FAILED for s in run.steps.values())
                    else WorkflowStatus.COMPLETED
                )
                await self.store.save(run)
                return run

            waiting = [
                s for s in run.steps.values()
                if s.status == StepStatus.WAITING_APPROVAL
            ]
            pending = [
                step for step in definition.steps
                if run.steps[step.id].status == StepStatus.PENDING
            ]

            ready: list[WorkflowStep] = []
            progress = False

            for step in pending:
                deps = [run.steps[d] for d in step.depends_on]

                if any(dep.status == StepStatus.FAILED for dep in deps):
                    run.steps[step.id].status = StepStatus.SKIPPED
                    progress = True
                    continue

                if all(dep.status in {StepStatus.COMPLETED, StepStatus.SKIPPED} for dep in deps):
                    if not self._condition_passes(step, run):
                        run.steps[step.id].status = StepStatus.SKIPPED
                        progress = True
                    else:
                        ready.append(step)

            if ready:
                results = await asyncio.gather(
                    *(self._execute_step(step, run) for step in ready)
                )
                for step_id, state in results:
                    run.steps[step_id] = state
                    if state.status == StepStatus.COMPLETED:
                        run.context[f"step.{step_id}"] = state.output
                progress = True
                await self.store.save(run)
                continue

            if waiting and not progress:
                run.status = WorkflowStatus.PAUSED
                await self.store.save(run)
                return run

            if not progress:
                run.status = WorkflowStatus.FAILED
                await self.store.save(run)
                return run

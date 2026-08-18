import asyncio
import pytest
from pydantic import ValidationError

from app.tools.approvals import ApprovalStore
from app.tools.audit import InMemoryToolAuditLog
from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.policy import ToolPolicy
from app.workflows.engine import WorkflowEngine
from app.workflows.models import (
    StepStatus,
    StepType,
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowStep,
)
from app.workflows.store import InMemoryWorkflowRunStore


def make_engine(agent_runner=None):
    approvals = ApprovalStore()
    executor = ToolExecutor(
        build_default_registry(),
        ToolPolicy(approvals),
        InMemoryToolAuditLog(),
    )

    async def default_agent(payload):
        return {"ok": True, "step": payload["step_id"]}

    return WorkflowEngine(
        store=InMemoryWorkflowRunStore(),
        tool_executor=executor,
        agent_runner=agent_runner or default_agent,
        max_parallel=4,
    ), approvals


@pytest.mark.asyncio
async def test_dag_dependencies_execute_in_order():
    engine, _ = make_engine()
    wf = WorkflowDefinition(
        name="dag",
        steps=[
            WorkflowStep(id="a", type=StepType.NOOP, input={"value": 1}),
            WorkflowStep(id="b", type=StepType.NOOP, depends_on=["a"], input={"value": 2}),
        ],
    )
    run = await engine.start(wf)
    assert run.status == WorkflowStatus.COMPLETED
    assert run.steps["a"].status == StepStatus.COMPLETED
    assert run.steps["b"].status == StepStatus.COMPLETED


def test_workflow_rejects_dependency_cycles():
    with pytest.raises(ValidationError):
        WorkflowDefinition(
            name="cycle",
            steps=[
                WorkflowStep(id="a", type=StepType.NOOP, depends_on=["b"]),
                WorkflowStep(id="b", type=StepType.NOOP, depends_on=["a"]),
            ],
        )


@pytest.mark.asyncio
async def test_condition_can_skip_step():
    engine, _ = make_engine()
    wf = WorkflowDefinition(
        name="condition",
        steps=[
            WorkflowStep(
                id="conditional",
                type=StepType.NOOP,
                condition_key="enabled",
                condition_equals=True,
            )
        ],
    )
    run = await engine.start(wf, {"enabled": False})
    assert run.status == WorkflowStatus.COMPLETED
    assert run.steps["conditional"].status == StepStatus.SKIPPED


@pytest.mark.asyncio
async def test_agent_step_retries_then_succeeds():
    attempts = 0

    async def flaky(payload):
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("temporary")
        return "done"

    engine, _ = make_engine(flaky)
    wf = WorkflowDefinition(
        name="retry",
        steps=[
            WorkflowStep(id="agent", type=StepType.AGENT, max_retries=1)
        ],
    )
    run = await engine.start(wf)
    assert run.status == WorkflowStatus.COMPLETED
    assert run.steps["agent"].attempts == 2
    assert run.steps["agent"].output == "done"


@pytest.mark.asyncio
async def test_parallel_ready_steps_execute_concurrently():
    started = 0
    release = asyncio.Event()

    async def runner(payload):
        nonlocal started
        started += 1
        if started == 2:
            release.set()
        await asyncio.wait_for(release.wait(), timeout=1)
        return payload["step_id"]

    engine, _ = make_engine(runner)
    wf = WorkflowDefinition(
        name="parallel",
        steps=[
            WorkflowStep(id="a", type=StepType.AGENT),
            WorkflowStep(id="b", type=StepType.AGENT),
        ],
    )
    run = await engine.start(wf)
    assert run.status == WorkflowStatus.COMPLETED
    assert started == 2


@pytest.mark.asyncio
async def test_tool_step_pauses_for_approval():
    engine, _ = make_engine()
    wf = WorkflowDefinition(
        name="approval",
        steps=[
            WorkflowStep(
                id="write",
                type=StepType.TOOL,
                input={
                    "tool": "artifact.write",
                    "arguments": {"name": "x.txt", "content": "hello"},
                },
            )
        ],
    )
    run = await engine.start(wf)
    assert run.status == WorkflowStatus.PAUSED
    assert run.steps["write"].status == StepStatus.WAITING_APPROVAL

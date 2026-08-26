import pytest

from app.llm.base import LLMProvider, LLMRequest
from app.llm.mock import MockLLMProvider
from app.runtime.registry import ConnectorRegistry
from app.tools.approvals import InMemoryApprovalStore
from app.tools.audit import InMemoryToolAuditLog
from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.policy import ToolPolicy
from app.workflows.engine import WorkflowEngine
from app.workflows.handlers import build_llm_agent_runner
from app.workflows.models import StepStatus, StepType, WorkflowDefinition, WorkflowStep
from app.workflows.store import InMemoryWorkflowRunStore


class RecordingProvider(LLMProvider):
    def __init__(self):
        self.requests = []

    async def generate(self, request: LLMRequest) -> str:
        self.requests.append(request)
        return f"echo:{request.prompt}"


def make_engine(*, agent_runner=None, connector_registry=None):
    approvals = InMemoryApprovalStore()
    executor = ToolExecutor(
        build_default_registry(),
        ToolPolicy(approvals),
        InMemoryToolAuditLog(),
    )
    return WorkflowEngine(
        store=InMemoryWorkflowRunStore(),
        tool_executor=executor,
        agent_runner=agent_runner or build_llm_agent_runner(MockLLMProvider()),
        connector_registry=connector_registry,
    )


@pytest.mark.asyncio
async def test_llm_agent_runner_calls_provider_and_returns_output():
    provider = RecordingProvider()
    runner = build_llm_agent_runner(provider)

    result = await runner({"step_id": "s1", "input": {"prompt": "summarize this"}})

    assert result == {"output": "echo:summarize this"}
    assert provider.requests[0].prompt == "summarize this"


@pytest.mark.asyncio
async def test_llm_agent_runner_requires_prompt():
    runner = build_llm_agent_runner(RecordingProvider())

    with pytest.raises(ValueError, match="input.prompt"):
        await runner({"step_id": "s1", "input": {}})


@pytest.mark.asyncio
async def test_agent_step_is_backed_by_llm_provider_in_engine():
    provider = RecordingProvider()
    engine = make_engine(agent_runner=build_llm_agent_runner(provider))
    definition = WorkflowDefinition(
        name="agent-workflow",
        steps=[WorkflowStep(id="ask", type=StepType.AGENT, input={"prompt": "plan the release"})],
    )

    run = await engine.start(definition)

    assert run.steps["ask"].status == StepStatus.COMPLETED
    assert run.steps["ask"].output == {"output": "echo:plan the release"}


@pytest.mark.asyncio
async def test_integration_step_executes_via_connector_registry():
    class FakeAdapter:
        def __init__(self):
            self.calls = []

        async def execute(self, request):
            self.calls.append(request)
            from app.integrations.models import IntegrationResult

            return IntegrationResult(
                provider="n8n", workflow=request.workflow, success=True, data={"ok": True}
            )

    adapter = FakeAdapter()
    registry = ConnectorRegistry()
    registry.register("n8n", adapter)
    engine = make_engine(connector_registry=registry)
    definition = WorkflowDefinition(
        name="integration-workflow",
        steps=[
            WorkflowStep(
                id="notify",
                type=StepType.INTEGRATION,
                input={"provider": "n8n", "workflow": "notify", "payload": {"x": 1}},
            )
        ],
    )

    run = await engine.start(definition)

    assert run.steps["notify"].status == StepStatus.COMPLETED
    assert run.steps["notify"].output == {"ok": True}
    assert adapter.calls[0].workflow == "notify"


@pytest.mark.asyncio
async def test_integration_step_unknown_provider_fails_step():
    engine = make_engine(connector_registry=ConnectorRegistry())
    definition = WorkflowDefinition(
        name="integration-workflow",
        steps=[
            WorkflowStep(
                id="notify",
                type=StepType.INTEGRATION,
                input={"provider": "missing"},
            )
        ],
    )

    run = await engine.start(definition)

    assert run.steps["notify"].status == StepStatus.FAILED

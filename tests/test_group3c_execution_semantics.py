import asyncio

import pytest
from fastapi.testclient import TestClient

from app.llm.base import LLMProvider, LLMRequest
from app.main import app
from app.memory.in_memory import InMemoryMemoryStore
from app.memory.models import MemoryScope, MemoryWrite
from app.memory.service import MemoryService
from app.services.llm_agents import ParallelAgentExecutor, SpecialistJob
from app.services.llm_verifier import LLMVerifier
from app.services.phase5_runtime import LLMPlanner, execute_phase5

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-api-key"}


class MalformedPlannerProvider(LLMProvider):
    async def generate(self, request: LLMRequest) -> str:
        return "this is not json"


class FlakyProvider(LLMProvider):
    """First specialist call always fails; everything else succeeds."""

    def __init__(self):
        self.calls = 0

    async def generate(self, request: LLMRequest) -> str:
        if "planning agent" in request.system:
            return (
                '{"jobs":['
                '{"name":"a","task":"task a"},'
                '{"name":"b","task":"task b"}'
                "]}"
            )
        if "verification agent" in request.system:
            return "Approved: good enough"
        if "final synthesis agent" in request.system:
            return "FINAL: done"
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("provider unavailable")
        return f"SPECIALIST: {request.prompt}"


class HangingProvider(LLMProvider):
    async def generate(self, request: LLMRequest) -> str:
        await asyncio.sleep(10)
        return "never"


@pytest.mark.asyncio
async def test_planner_malformed_output_raises_value_error():
    with pytest.raises(ValueError):
        await LLMPlanner(MalformedPlannerProvider()).create_plan("Build something")


@pytest.mark.asyncio
async def test_planner_enforces_job_limit():
    class ManyJobsProvider(LLMProvider):
        async def generate(self, request: LLMRequest) -> str:
            jobs = [{"name": f"j{i}", "task": f"task {i}"} for i in range(10)]
            return __import__("json").dumps({"jobs": jobs})

    plan = await LLMPlanner(ManyJobsProvider(), max_jobs=3).create_plan("Build something")
    assert len(plan.jobs) == 3


@pytest.mark.asyncio
async def test_specialist_failure_is_isolated_from_other_specialists():
    provider = FlakyProvider()
    executor = ParallelAgentExecutor(provider, max_parallel=2, max_retries=0)
    results = await executor.run([SpecialistJob("a", "task a"), SpecialistJob("b", "task b")])

    by_name = {r.name: r for r in results}
    assert by_name["a"].error is not None
    assert by_name["a"].output == ""
    assert by_name["b"].error is None
    assert by_name["b"].output.startswith("SPECIALIST:")


@pytest.mark.asyncio
async def test_verifier_rejects_when_response_does_not_approve():
    class RejectingProvider(LLMProvider):
        async def generate(self, request: LLMRequest) -> str:
            return "Rejected: missing test coverage"

    from app.services.llm_agents import SpecialistResult

    verifier = LLMVerifier(RejectingProvider())
    verification = await verifier.verify(
        "objective", [SpecialistResult("a", "some output", 1)]
    )
    assert verification.approved is False
    assert "Rejected" in verification.feedback


@pytest.mark.asyncio
async def test_context_injection_includes_relevant_memory(monkeypatch):
    memory_service = MemoryService(InMemoryMemoryStore())
    await memory_service.remember(
        MemoryWrite(
            scope=MemoryScope.PROJECT,
            key="prior-decision",
            content="Use FastAPI for the backend",
            project_id="agent-os",
        )
    )

    captured = {}

    class CapturingProvider(LLMProvider):
        async def generate(self, request: LLMRequest) -> str:
            if "planning agent" in request.system:
                captured["prompt"] = request.prompt
                return '{"jobs":[{"name":"a","task":"task a"}]}'
            if "verification agent" in request.system:
                return "Approved: fine"
            if "final synthesis agent" in request.system:
                return "FINAL: done"
            return "SPECIALIST: ok"

    monkeypatch.setattr(
        "app.services.phase5_runtime.build_llm_provider", lambda: CapturingProvider()
    )

    await execute_phase5(
        "Design the backend",
        project_id="agent-os",
        memory_service=memory_service,
    )

    assert "Use FastAPI for the backend" in captured["prompt"]


@pytest.mark.asyncio
async def test_autonomous_run_times_out_on_hanging_provider(monkeypatch):
    monkeypatch.setattr(
        "app.services.phase5_runtime.build_llm_provider", lambda: HangingProvider()
    )
    monkeypatch.setattr("app.api.phase5.settings.autonomous_timeout_seconds", 0.05)

    response = client.post(
        "/api/v1/autonomous/run",
        headers=AUTH_HEADERS,
        json={"objective": "Build something that will hang"},
    )

    assert response.status_code == 504

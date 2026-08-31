import pytest

from app.llm.mock import MockLLMProvider
from app.services.llm_agents import ParallelAgentExecutor, SpecialistJob
from app.services.phase3_runtime import execute_phase3


@pytest.mark.asyncio
async def test_parallel_specialists_return_results():
    executor = ParallelAgentExecutor(MockLLMProvider(), max_parallel=3)
    jobs = [
        SpecialistJob("research", "Research the requirement"),
        SpecialistJob("builder", "Build the solution"),
        SpecialistJob("tester", "Test the solution"),
    ]
    results = await executor.run(jobs)
    assert len(results) == 3
    assert all(result.output.startswith("MOCK_RESULT:") for result in results)

@pytest.mark.asyncio
async def test_phase3_runtime_verifies_results(monkeypatch):
    monkeypatch.setenv("AGENT_OS_LLM_PROVIDER", "mock")
    result = await execute_phase3(
        "Create and verify a feature",
        ["Plan it", "Implement it", "Test it"],
    )
    assert len(result["results"]) == 3
    assert result["verification"]["approved"] is True

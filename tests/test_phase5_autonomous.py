import json

import pytest

from app.llm.base import LLMProvider, LLMRequest
from app.services.phase5_runtime import LLMPlanner, execute_phase5


class Phase5Provider(LLMProvider):
    async def generate(self, request: LLMRequest) -> str:
        if "planning agent" in request.system:
            return json.dumps({"jobs": [
                {"name": "researcher", "task": "Research requirements", "system_prompt": "Research specialist"},
                {"name": "builder", "task": "Design implementation", "system_prompt": "Engineering specialist"},
                {"name": "tester", "task": "Define verification", "system_prompt": "QA specialist"},
            ]})
        if "verification agent" in request.system:
            return "Approved: specialist outputs cover the objective."
        if "final synthesis agent" in request.system:
            return "FINAL: consolidated solution"
        return f"SPECIALIST: {request.prompt}"


@pytest.mark.asyncio
async def test_llm_planner_creates_dynamic_jobs():
    plan = await LLMPlanner(Phase5Provider()).create_plan("Build a feature")
    assert [job.name for job in plan.jobs] == ["researcher", "builder", "tester"]
    assert plan.jobs[1].task == "Design implementation"


@pytest.mark.asyncio
async def test_phase5_end_to_end(monkeypatch):
    monkeypatch.setattr("app.services.phase5_runtime.build_llm_provider", lambda: Phase5Provider())
    result = await execute_phase5("Build and validate a feature", "Python API")
    assert len(result["plan"]["jobs"]) == 3
    assert len(result["results"]) == 3
    assert result["verification"]["approved"] is True
    assert result["final_answer"] == "FINAL: consolidated solution"

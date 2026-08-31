import pytest

from app.core.orchestrator import Orchestrator
from app.models.orchestration import OrchestrationRequest


@pytest.mark.asyncio
async def test_orchestration():
    result=await Orchestrator().run(OrchestrationRequest(objective="Build a customer support workflow"))
    assert len(result.results)==3
    assert result.verification.passed
    assert {r.role.value for r in result.results}=={"researcher","builder","reviewer"}

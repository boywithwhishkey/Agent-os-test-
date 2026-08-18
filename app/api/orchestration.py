from fastapi import APIRouter
from app.core.orchestrator import Orchestrator
from app.models.orchestration import OrchestrationRequest, OrchestrationResult
router=APIRouter(prefix="/api/v1", tags=["orchestration"])
orchestrator=Orchestrator()
@router.post("/orchestrate", response_model=OrchestrationResult)
async def orchestrate(payload: OrchestrationRequest):
    return await orchestrator.run(payload)

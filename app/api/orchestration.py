from fastapi import APIRouter, Depends

from app.core.auth import require_api_key
from app.core.orchestrator import Orchestrator
from app.models.orchestration import OrchestrationRequest, OrchestrationResult

router = APIRouter(prefix="/api/v1", tags=["orchestration"])
orchestrator = Orchestrator()


@router.post(
    "/orchestrate",
    response_model=OrchestrationResult,
    dependencies=[Depends(require_api_key)],
)
async def orchestrate(
    payload: OrchestrationRequest,
):
    return await orchestrator.run(payload)

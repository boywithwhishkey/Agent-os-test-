import os
import secrets

from fastapi import APIRouter, Header, HTTPException

from app.core.orchestrator import Orchestrator
from app.models.orchestration import OrchestrationRequest, OrchestrationResult


router = APIRouter(prefix="/api/v1", tags=["orchestration"])
orchestrator = Orchestrator()


@router.post("/orchestrate", response_model=OrchestrationResult)
async def orchestrate(
    payload: OrchestrationRequest,
    x_api_key: str | None = Header(default=None),
):
    expected_key = os.getenv("AGENT_OS_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="API authentication is not configured",
        )

    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

    return await orchestrator.run(payload)

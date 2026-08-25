from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import require_api_key
from app.core.correlation import get_or_create_correlation_id
from app.integrations.factory import build_integration_adapter
from app.integrations.models import IntegrationRequest, IntegrationResult

router = APIRouter(
    prefix="/api/v1/integrations",
    tags=["integrations"],
    dependencies=[Depends(require_api_key)],
)


class IntegrationExecutePayload(BaseModel):
    provider: str = Field(default="n8n")
    request: IntegrationRequest


@router.post("/execute", response_model=IntegrationResult)
async def execute_integration(payload: IntegrationExecutePayload) -> IntegrationResult:
    request = payload.request.model_copy(
        update={"correlation_id": get_or_create_correlation_id(payload.request.correlation_id)}
    )
    try:
        adapter = build_integration_adapter(payload.provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await adapter.execute(request)

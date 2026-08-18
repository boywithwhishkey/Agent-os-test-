from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.integrations.factory import build_integration_adapter
from app.integrations.models import IntegrationRequest, IntegrationResult

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


class IntegrationExecutePayload(BaseModel):
    provider: str = Field(default="n8n")
    request: IntegrationRequest


@router.post("/execute", response_model=IntegrationResult)
async def execute_integration(payload: IntegrationExecutePayload) -> IntegrationResult:
    try:
        adapter = build_integration_adapter(payload.provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await adapter.execute(payload.request)

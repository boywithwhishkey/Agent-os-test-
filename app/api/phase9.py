from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import require_api_key
from app.core.correlation import get_or_create_correlation_id
from app.integrations.factory import (
    build_integration_adapter,
    is_provider_configured,
    list_providers,
    provider_display_name,
    provider_requirements,
)
from app.integrations.models import IntegrationRequest, IntegrationResult, IntegrationStatus
from app.integrations.status_store import IntegrationStatusStore

router = APIRouter(
    prefix="/api/v1/integrations",
    tags=["integrations"],
    dependencies=[Depends(require_api_key)],
)
status_store = IntegrationStatusStore()


class IntegrationExecutePayload(BaseModel):
    provider: str = Field(default="n8n")
    request: IntegrationRequest


@router.get("", response_model=list[IntegrationStatus])
async def list_integrations() -> list[IntegrationStatus]:
    statuses: list[IntegrationStatus] = []
    for provider in list_providers():
        record = status_store.get(provider.value)
        statuses.append(
            IntegrationStatus(
                provider=provider,
                name=provider_display_name(provider),
                configured=is_provider_configured(provider),
                requires=provider_requirements(provider),
                connected=record.connected,
                last_check=record.last_check,
                last_check_latency_ms=record.last_check_latency_ms,
                last_check_error=record.last_check_error,
                last_execution=record.last_execution,
                last_execution_success=record.last_execution_success,
            )
        )
    return statuses


@router.post("/{provider}/test", response_model=IntegrationStatus)
async def test_integration(provider: str) -> IntegrationStatus:
    normalized = provider.lower().strip()
    try:
        candidates = [p for p in list_providers() if p.value == normalized]
        provider_enum = candidates[0]
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Unknown integration provider: {provider}") from None

    if not is_provider_configured(provider_enum):
        requires = ", ".join(provider_requirements(provider_enum))
        raise HTTPException(
            status_code=503,
            detail=f"{provider_display_name(provider_enum)} is not configured. Set {requires}.",
        )

    try:
        adapter = build_integration_adapter(provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    connected, latency_ms, error = await adapter.test_connection()
    status_store.record_check(normalized, connected=connected, latency_ms=latency_ms, error=error)
    record = status_store.get(normalized)
    return IntegrationStatus(
        provider=provider_enum,
        name=provider_display_name(provider_enum),
        configured=True,
        requires=provider_requirements(provider_enum),
        connected=record.connected,
        last_check=record.last_check,
        last_check_latency_ms=record.last_check_latency_ms,
        last_check_error=record.last_check_error,
        last_execution=record.last_execution,
        last_execution_success=record.last_execution_success,
    )


@router.post("/execute", response_model=IntegrationResult)
async def execute_integration(payload: IntegrationExecutePayload) -> IntegrationResult:
    request = payload.request.model_copy(
        update={"correlation_id": get_or_create_correlation_id(payload.request.correlation_id)}
    )
    try:
        adapter = build_integration_adapter(payload.provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = await adapter.execute(request)
    status_store.record_execution(payload.provider.lower().strip(), success=result.success)
    return result

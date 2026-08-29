from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_api_key
from app.core.correlation import get_or_create_correlation_id
from app.runtime.factory import build_runtime
from app.runtime.models import (
    CircuitBreakerStatus,
    RateLimitStatus,
    RuntimeExecution,
    RuntimeRequest,
    RuntimeStatus,
)

router = APIRouter(
    prefix="/api/v1/runtime",
    tags=["runtime"],
    dependencies=[Depends(require_api_key)],
)
runtime = build_runtime()

@router.post("/execute", response_model=RuntimeExecution)
async def execute_runtime(payload: RuntimeRequest) -> RuntimeExecution:
    request = payload.model_copy(
        update={"correlation_id": get_or_create_correlation_id(payload.correlation_id)}
    )
    return await runtime.execute(request)

@router.get("/status", response_model=RuntimeStatus)
async def get_runtime_status(provider: str, workflow: str) -> RuntimeStatus:
    key = f"{provider}:{workflow}"
    return RuntimeStatus(
        provider=provider,
        workflow=workflow,
        circuit_breaker=CircuitBreakerStatus(**runtime.circuit_breaker.status(key)),
        rate_limit=RateLimitStatus(**runtime.rate_limiter.usage(key)),
    )

@router.get("/executions/{execution_id}", response_model=RuntimeExecution)
async def get_execution(execution_id: str) -> RuntimeExecution:
    execution = await runtime.store.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

from fastapi import APIRouter, HTTPException
from app.runtime.factory import build_runtime
from app.runtime.models import RuntimeExecution, RuntimeRequest

router = APIRouter(prefix="/api/v1/runtime", tags=["runtime"])
runtime = build_runtime()

@router.post("/execute", response_model=RuntimeExecution)
async def execute_runtime(payload: RuntimeRequest) -> RuntimeExecution:
    return await runtime.execute(payload)

@router.get("/executions/{execution_id}", response_model=RuntimeExecution)
async def get_execution(execution_id: str) -> RuntimeExecution:
    execution = await runtime.store.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

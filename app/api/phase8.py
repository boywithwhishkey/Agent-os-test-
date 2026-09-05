from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.auth import require_api_key
from app.workflows.factory import build_workflow_definition_store, build_workflow_engine
from app.workflows.models import WorkflowDefinition, WorkflowRun

router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["workflows"],
    dependencies=[Depends(require_api_key)],
)
engine = build_workflow_engine()
definitions = build_workflow_definition_store()


class WorkflowStartRequest(BaseModel):
    definition: WorkflowDefinition
    context: dict = Field(default_factory=dict)


class WorkflowResumeRequest(BaseModel):
    approvals: dict[str, str] = Field(default_factory=dict)


@router.post("/run", response_model=WorkflowRun)
async def run_workflow(payload: WorkflowStartRequest, request: Request) -> WorkflowRun:
    await definitions.save(payload.definition)
    return await engine.start(
        payload.definition,
        payload.context,
        correlation_id=request.state.correlation_id,
    )


@router.post("/runs/{run_id}/resume", response_model=WorkflowRun)
async def resume_workflow(run_id: str, payload: WorkflowResumeRequest) -> WorkflowRun:
    run = await engine.store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    definition = await definitions.get(run.workflow_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Workflow definition not found")
    return await engine.resume(definition, run_id, approvals=payload.approvals)


@router.get("/runs/{run_id}", response_model=WorkflowRun)
async def get_workflow_run(run_id: str) -> WorkflowRun:
    run = await engine.store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run

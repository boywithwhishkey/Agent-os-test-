from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.workflows.factory import build_workflow_engine
from app.workflows.models import WorkflowDefinition, WorkflowRun

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])
engine = build_workflow_engine()
definitions: dict[str, WorkflowDefinition] = {}


class WorkflowStartRequest(BaseModel):
    definition: WorkflowDefinition
    context: dict = Field(default_factory=dict)


class WorkflowResumeRequest(BaseModel):
    approvals: dict[str, str] = Field(default_factory=dict)


@router.post("/run", response_model=WorkflowRun)
async def run_workflow(payload: WorkflowStartRequest) -> WorkflowRun:
    definitions[payload.definition.id] = payload.definition
    return await engine.start(payload.definition, payload.context)


@router.post("/runs/{run_id}/resume", response_model=WorkflowRun)
async def resume_workflow(run_id: str, payload: WorkflowResumeRequest) -> WorkflowRun:
    run = await engine.store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    definition = definitions.get(run.workflow_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Workflow definition not found")
    return await engine.resume(definition, run_id, approvals=payload.approvals)


@router.get("/runs/{run_id}", response_model=WorkflowRun)
async def get_workflow_run(run_id: str) -> WorkflowRun:
    run = await engine.store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run

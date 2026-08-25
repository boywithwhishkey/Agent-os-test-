import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.auth import require_api_key
from app.core.config import settings
from app.services.phase5_runtime import execute_phase5

router = APIRouter(
    prefix="/api/v1",
    tags=["phase5"],
    dependencies=[Depends(require_api_key)],
)


class AutonomousRunRequest(BaseModel):
    objective: str = Field(min_length=3)
    context: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None


@router.post("/autonomous/run")
async def autonomous_run(payload: AutonomousRunRequest) -> dict:
    return await asyncio.wait_for(
        execute_phase5(
            payload.objective,
            payload.context,
            project_id=payload.project_id,
            task_id=payload.task_id,
            session_id=payload.session_id,
        ),
        timeout=settings.autonomous_timeout_seconds,
    )

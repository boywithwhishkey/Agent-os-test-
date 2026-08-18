from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.services.phase5_runtime import execute_phase5

router = APIRouter(prefix="/api/v1", tags=["phase5"])


class AutonomousRunRequest(BaseModel):
    objective: str = Field(min_length=3)
    context: str | None = None


@router.post("/autonomous/run")
async def autonomous_run(payload: AutonomousRunRequest) -> dict:
    return await execute_phase5(payload.objective, payload.context)

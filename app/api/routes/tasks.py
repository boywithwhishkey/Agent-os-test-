from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import require_api_key
from app.models.task import Task, TaskCreate
from app.services.task_factory import build_task_service

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(require_api_key)],
)
task_service = build_task_service()


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate) -> Task:
    return await task_service.create(payload)


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str) -> Task:
    task = await task_service.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

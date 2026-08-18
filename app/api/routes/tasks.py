from fastapi import APIRouter, HTTPException, status

from app.models.task import Task, TaskCreate
from app.services.task_service import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    return task_service.create(payload)


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str) -> Task:
    task = task_service.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

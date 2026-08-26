from app.models.task import Task, TaskCreate
from app.services.task_store import TaskStore


class TaskService:
    def __init__(self, store: TaskStore) -> None:
        self.store = store

    async def create(self, payload: TaskCreate) -> Task:
        task = Task(
            objective=payload.objective,
            priority=payload.priority,
            project_id=payload.project_id,
        )
        await self.store.save(task)
        return task

    async def get(self, task_id: str) -> Task | None:
        return await self.store.get(task_id)

from app.models.task import Task, TaskCreate


class TaskService:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def create(self, payload: TaskCreate) -> Task:
        task = Task(
            objective=payload.objective,
            priority=payload.priority,
            project_id=payload.project_id,
        )
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)


task_service = TaskService()

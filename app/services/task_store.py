from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.task import Task


class TaskStore(ABC):
    @abstractmethod
    async def save(self, task: Task) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, task_id: str) -> Task | None:
        raise NotImplementedError


class InMemoryTaskStore(TaskStore):
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    async def save(self, task: Task) -> None:
        self._tasks[task.id] = task.model_copy(deep=True)

    async def get(self, task_id: str) -> Task | None:
        task = self._tasks.get(task_id)
        return task.model_copy(deep=True) if task else None

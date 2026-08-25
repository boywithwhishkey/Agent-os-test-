from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class QueueJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    queue: str = "default"
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    attempts: int = 0


class JobQueue(ABC):
    @abstractmethod
    async def enqueue(self, job: QueueJob) -> str:
        raise NotImplementedError

    @abstractmethod
    async def dequeue(self, queue: str = "default", timeout: int = 1) -> QueueJob | None:
        raise NotImplementedError


class InMemoryJobQueue(JobQueue):
    def __init__(self) -> None:
        self._queues: dict[str, deque[QueueJob]] = {}

    async def enqueue(self, job: QueueJob) -> str:
        self._queues.setdefault(job.queue, deque()).append(job.model_copy(deep=True))
        return job.id

    async def dequeue(self, queue: str = "default", timeout: int = 1) -> QueueJob | None:
        del timeout
        items = self._queues.setdefault(queue, deque())
        return items.popleft() if items else None

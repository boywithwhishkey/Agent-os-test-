from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from time import monotonic
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

    async def claim_once(self, key: str, ttl_seconds: int = 86_400) -> bool:
        """Claim a delivery id; duplicate claims return False.

        The base implementation is intentionally safe for local development.
        Redis overrides it with an atomic SET NX so multiple workers share the
        same replay guard in a durable deployment.
        """
        del key, ttl_seconds
        return True


class InMemoryJobQueue(JobQueue):
    def __init__(self) -> None:
        self._queues: dict[str, deque[QueueJob]] = {}
        self._claims: dict[str, float] = {}

    async def enqueue(self, job: QueueJob) -> str:
        self._queues.setdefault(job.queue, deque()).append(job.model_copy(deep=True))
        return job.id

    async def dequeue(self, queue: str = "default", timeout: int = 1) -> QueueJob | None:
        del timeout
        items = self._queues.setdefault(queue, deque())
        return items.popleft() if items else None

    async def claim_once(self, key: str, ttl_seconds: int = 86_400) -> bool:
        now = monotonic()
        expired = [claim for claim, expires in self._claims.items() if expires <= now]
        for claim in expired:
            self._claims.pop(claim, None)
        if key in self._claims:
            return False
        self._claims[key] = now + ttl_seconds
        return True

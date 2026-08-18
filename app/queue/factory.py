from __future__ import annotations

import os

from app.queue.base import InMemoryJobQueue, JobQueue
from app.queue.redis_queue import RedisJobQueue


def build_job_queue() -> JobQueue:
    backend = os.getenv("AGENT_OS_QUEUE_BACKEND", "memory").lower().strip()
    if backend == "memory":
        return InMemoryJobQueue()
    if backend == "redis":
        return RedisJobQueue.from_env()
    raise RuntimeError(f"Unsupported queue backend: {backend}")

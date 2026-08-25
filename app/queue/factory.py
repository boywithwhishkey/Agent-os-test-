from __future__ import annotations

from app.core.config import settings
from app.core.lifecycle import register_resource
from app.queue.base import InMemoryJobQueue, JobQueue
from app.queue.redis_queue import RedisJobQueue


def build_job_queue() -> JobQueue:
    backend = settings.queue_backend.lower().strip()
    if backend == "memory":
        return InMemoryJobQueue()
    if backend == "redis":
        return register_resource(RedisJobQueue.from_settings())
    raise RuntimeError(f"Unsupported queue backend: {backend}")

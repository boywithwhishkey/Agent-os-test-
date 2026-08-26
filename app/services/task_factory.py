from __future__ import annotations

from app.core.config import settings
from app.core.lifecycle import register_resource
from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import PostgresTaskStore
from app.services.task_service import TaskService
from app.services.task_store import InMemoryTaskStore, TaskStore


def build_task_store() -> TaskStore:
    backend = settings.task_backend.lower().strip()
    if backend == "memory":
        return InMemoryTaskStore()
    if backend == "postgres":
        database = register_resource(AsyncpgDatabase.from_settings())
        return PostgresTaskStore(database)
    raise RuntimeError(f"Unsupported task backend: {backend}")


def build_task_service() -> TaskService:
    return TaskService(build_task_store())

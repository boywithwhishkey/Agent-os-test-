from __future__ import annotations

from app.core.config import settings
from app.core.lifecycle import register_resource
from app.memory.in_memory import InMemoryMemoryStore
from app.memory.service import MemoryService
from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import PostgresMemoryStore


def build_memory_service() -> MemoryService:
    backend = settings.memory_backend.lower().strip()

    if backend == "memory":
        return MemoryService(InMemoryMemoryStore())

    if backend in {"postgres", "postgres_pgvector"}:
        database = register_resource(AsyncpgDatabase.from_settings())
        return MemoryService(PostgresMemoryStore(database))

    raise RuntimeError(
        f"Unsupported memory backend: {backend}. "
        "Supported backends: memory, postgres, postgres_pgvector."
    )

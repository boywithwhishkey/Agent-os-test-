from __future__ import annotations

import os

from app.memory.in_memory import InMemoryMemoryStore
from app.memory.service import MemoryService
from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import PostgresMemoryStore


def build_memory_service() -> MemoryService:
    backend = os.getenv("AGENT_OS_MEMORY_BACKEND", "memory").lower().strip()

    if backend == "memory":
        return MemoryService(InMemoryMemoryStore())

    if backend in {"postgres", "postgres_pgvector"}:
        database = AsyncpgDatabase.from_env()
        return MemoryService(PostgresMemoryStore(database))

    raise RuntimeError(
        f"Unsupported memory backend: {backend}. "
        "Supported backends: memory, postgres, postgres_pgvector."
    )

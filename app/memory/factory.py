from __future__ import annotations

import os

from app.memory.in_memory import InMemoryMemoryStore
from app.memory.service import MemoryService


def build_memory_service() -> MemoryService:
    backend = os.getenv("AGENT_OS_MEMORY_BACKEND", "memory").lower().strip()
    if backend == "memory":
        return MemoryService(InMemoryMemoryStore())

    # Future adapters:
    # - postgres
    # - postgres_pgvector
    # - redis_cache + postgres
    raise RuntimeError(
        f"Unsupported memory backend: {backend}. "
        "Supported backend for Phase 7: memory."
    )

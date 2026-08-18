from __future__ import annotations

from abc import ABC, abstractmethod

from app.memory.models import MemoryQuery, MemoryRecord, MemoryWrite


class MemoryStore(ABC):
    @abstractmethod
    async def write(self, memory: MemoryWrite) -> MemoryRecord:
        raise NotImplementedError

    @abstractmethod
    async def get(self, memory_id: str) -> MemoryRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[MemoryRecord]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        raise NotImplementedError

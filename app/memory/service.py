from __future__ import annotations

from app.memory.models import MemoryContext, MemoryQuery, MemoryRecord, MemoryWrite
from app.memory.store import MemoryStore


class MemoryService:
    def __init__(self, store: MemoryStore):
        self.store = store

    async def remember(self, memory: MemoryWrite) -> MemoryRecord:
        return await self.store.write(memory)

    async def recall(self, query: MemoryQuery) -> list[MemoryRecord]:
        return await self.store.search(query)

    async def build_context(self, query: MemoryQuery) -> MemoryContext:
        records = await self.recall(query)
        rendered = "\n\n".join(
            f"[{record.scope.value}:{record.key}] {record.content}"
            for record in records
        )
        return MemoryContext(records=records, rendered=rendered)

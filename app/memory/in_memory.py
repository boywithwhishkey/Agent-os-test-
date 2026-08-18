from __future__ import annotations

import re

from app.memory.models import MemoryQuery, MemoryRecord, MemoryWrite
from app.memory.store import MemoryStore


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", value.casefold())
        if len(token) >= 2
    }


class InMemoryMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}

    async def write(self, memory: MemoryWrite) -> MemoryRecord:
        record = MemoryRecord(**memory.model_dump())
        self._records[record.id] = record
        return record

    async def get(self, memory_id: str) -> MemoryRecord | None:
        return self._records.get(memory_id)

    async def search(self, query: MemoryQuery) -> list[MemoryRecord]:
        records = list(self._records.values())

        if query.scopes:
            allowed = set(query.scopes)
            records = [r for r in records if r.scope in allowed]
        if query.project_id is not None:
            records = [r for r in records if r.project_id == query.project_id]
        if query.task_id is not None:
            records = [r for r in records if r.task_id == query.task_id]
        if query.session_id is not None:
            records = [r for r in records if r.session_id == query.session_id]
        if query.agent is not None:
            records = [r for r in records if r.agent == query.agent]
        if query.tags:
            wanted = set(query.tags)
            records = [r for r in records if wanted.intersection(r.tags)]

        scored: list[tuple[int, MemoryRecord]] = []
        if query.query:
            query_tokens = _tokens(query.query)
            for record in records:
                haystack = " ".join(
                    [record.key, record.content, *record.tags]
                )
                record_tokens = _tokens(haystack)
                overlap = len(query_tokens.intersection(record_tokens))
                if overlap:
                    scored.append((overlap, record))

            scored.sort(
                key=lambda item: (
                    item[0],
                    item[1].importance,
                    item[1].created_at,
                ),
                reverse=True,
            )
            return [record for _, record in scored[: query.limit]]

        records.sort(key=lambda r: (r.importance, r.created_at), reverse=True)
        return records[: query.limit]

    async def delete(self, memory_id: str) -> bool:
        return self._records.pop(memory_id, None) is not None

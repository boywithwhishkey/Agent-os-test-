from __future__ import annotations

from app.memory.models import MemoryQuery, MemoryScope
from app.memory.service import MemoryService


class ContextInjector:
    def __init__(self, memory: MemoryService):
        self.memory = memory

    async def for_task(
        self,
        *,
        objective: str,
        project_id: str | None = None,
        task_id: str | None = None,
        session_id: str | None = None,
        limit: int = 12,
    ) -> str:
        context = await self.memory.build_context(
            MemoryQuery(
                query=objective,
                scopes=[
                    MemoryScope.PROJECT,
                    MemoryScope.DECISION,
                    MemoryScope.TASK,
                    MemoryScope.SESSION,
                    MemoryScope.AGENT_RUN,
                ],
                project_id=project_id,
                task_id=task_id,
                session_id=session_id,
                limit=limit,
            )
        )
        if not context.rendered:
            return ""
        return "RELEVANT MEMORY:\n" + context.rendered

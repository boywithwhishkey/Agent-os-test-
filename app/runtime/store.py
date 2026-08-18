from __future__ import annotations
from abc import ABC, abstractmethod
from app.runtime.models import RuntimeExecution

class ExecutionStore(ABC):
    @abstractmethod
    async def save(self, execution: RuntimeExecution) -> None: ...
    @abstractmethod
    async def get(self, execution_id: str) -> RuntimeExecution | None: ...
    @abstractmethod
    async def by_idempotency_key(self, key: str) -> RuntimeExecution | None: ...

class InMemoryExecutionStore(ExecutionStore):
    def __init__(self) -> None:
        self._items: dict[str, RuntimeExecution] = {}
        self._idempotency: dict[str, str] = {}

    async def save(self, execution: RuntimeExecution) -> None:
        self._items[execution.id] = execution.model_copy(deep=True)
        if execution.idempotency_key:
            self._idempotency[execution.idempotency_key] = execution.id

    async def get(self, execution_id: str) -> RuntimeExecution | None:
        item = self._items.get(execution_id)
        return item.model_copy(deep=True) if item else None

    async def by_idempotency_key(self, key: str) -> RuntimeExecution | None:
        execution_id = self._idempotency.get(key)
        return await self.get(execution_id) if execution_id else None

from __future__ import annotations

from abc import ABC, abstractmethod

from app.workflows.models import WorkflowDefinition


class WorkflowDefinitionStore(ABC):
    @abstractmethod
    async def save(self, definition: WorkflowDefinition) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, definition_id: str) -> WorkflowDefinition | None:
        raise NotImplementedError


class InMemoryWorkflowDefinitionStore(WorkflowDefinitionStore):
    def __init__(self) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}

    async def save(self, definition: WorkflowDefinition) -> None:
        self._definitions[definition.id] = definition.model_copy(deep=True)

    async def get(self, definition_id: str) -> WorkflowDefinition | None:
        definition = self._definitions.get(definition_id)
        return definition.model_copy(deep=True) if definition else None

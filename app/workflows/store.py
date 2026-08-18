from __future__ import annotations

from abc import ABC, abstractmethod

from app.workflows.models import WorkflowRun


class WorkflowRunStore(ABC):
    @abstractmethod
    async def save(self, run: WorkflowRun) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, run_id: str) -> WorkflowRun | None:
        raise NotImplementedError


class InMemoryWorkflowRunStore(WorkflowRunStore):
    def __init__(self) -> None:
        self._runs: dict[str, WorkflowRun] = {}

    async def save(self, run: WorkflowRun) -> None:
        self._runs[run.id] = run.model_copy(deep=True)

    async def get(self, run_id: str) -> WorkflowRun | None:
        run = self._runs.get(run_id)
        return run.model_copy(deep=True) if run else None

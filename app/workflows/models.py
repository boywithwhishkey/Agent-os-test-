from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class StepType(StrEnum):
    NOOP = "noop"
    TOOL = "tool"
    AGENT = "agent"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStep(BaseModel):
    id: str
    type: StepType
    depends_on: list[str] = Field(default_factory=list)
    input: dict[str, Any] = Field(default_factory=dict)
    condition_key: str | None = None
    condition_equals: Any = None
    max_retries: int = Field(default=0, ge=0, le=10)
    timeout_seconds: float = Field(default=30.0, gt=0, le=3600)


class WorkflowDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(min_length=1, max_length=200)
    steps: list[WorkflowStep] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self):
        ids = [step.id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("Workflow step ids must be unique")
        known = set(ids)
        for step in self.steps:
            missing = set(step.depends_on) - known
            if missing:
                raise ValueError(f"Unknown dependencies for {step.id}: {sorted(missing)}")
            if step.id in step.depends_on:
                raise ValueError(f"Step {step.id} cannot depend on itself")

        visiting: set[str] = set()
        visited: set[str] = set()
        deps = {step.id: step.depends_on for step in self.steps}

        def visit(node: str):
            if node in visiting:
                raise ValueError("Workflow contains a dependency cycle")
            if node in visited:
                return
            visiting.add(node)
            for dep in deps[node]:
                visit(dep)
            visiting.remove(node)
            visited.add(node)

        for node in ids:
            visit(node)
        return self


class StepRun(BaseModel):
    step_id: str
    status: StepStatus = StepStatus.PENDING
    attempts: int = 0
    output: Any = None
    error: str | None = None
    approval_id: str | None = None


class WorkflowRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: dict[str, Any] = Field(default_factory=dict)
    steps: dict[str, StepRun] = Field(default_factory=dict)

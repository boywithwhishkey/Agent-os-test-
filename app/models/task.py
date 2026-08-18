from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCreate(BaseModel):
    objective: str = Field(min_length=3, max_length=2000)
    priority: TaskPriority = TaskPriority.NORMAL
    project_id: str | None = None


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    project_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryScope(StrEnum):
    SESSION = "session"
    TASK = "task"
    PROJECT = "project"
    DECISION = "decision"
    AGENT_RUN = "agent_run"


class MemoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    scope: MemoryScope
    key: str
    content: str
    project_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    agent: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryWrite(BaseModel):
    scope: MemoryScope
    key: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50_000)
    project_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    agent: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class MemoryQuery(BaseModel):
    query: str | None = None
    scopes: list[MemoryScope] = Field(default_factory=list)
    project_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    agent: str | None = None
    tags: list[str] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)


class MemoryContext(BaseModel):
    records: list[MemoryRecord]
    rendered: str

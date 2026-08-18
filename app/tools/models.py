from __future__ import annotations

from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class ToolRisk(StrEnum):
    READ = "read"
    WRITE = "write"
    HIGH_RISK = "high_risk"


class ToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    approved: bool = False


class ToolExecutionResult(BaseModel):
    tool: str
    success: bool
    risk: ToolRisk
    output: Any = None
    error: str | None = None
    approval_required: bool = False

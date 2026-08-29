from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IntegrationProvider(StrEnum):
    N8N = "n8n"


class IntegrationRequest(BaseModel):
    workflow: str = Field(min_length=1, max_length=200)
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)


class IntegrationResult(BaseModel):
    provider: IntegrationProvider
    workflow: str
    success: bool
    status_code: int | None = None
    data: Any = None
    error: str | None = None
    correlation_id: str | None = None


class IntegrationStatus(BaseModel):
    provider: IntegrationProvider
    name: str
    configured: bool
    requires: list[str] = Field(default_factory=list)
    connected: bool | None = None
    last_check: str | None = None
    last_check_latency_ms: float | None = None
    last_check_error: str | None = None
    last_execution: str | None = None
    last_execution_success: bool | None = None

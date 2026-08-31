from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"

class RuntimeRequest(BaseModel):
    provider: str
    workflow: str
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    correlation_id: str | None = None
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    max_retries: int = Field(default=2, ge=0, le=10)

class RuntimeExecution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    provider: str
    workflow: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    attempts: int = 0
    correlation_id: str | None = None
    idempotency_key: str | None = None
    data: Any = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class CircuitBreakerStatus(BaseModel):
    state: str
    failures: int
    recovers_in_seconds: float | None = None

class RateLimitStatus(BaseModel):
    used: int
    limit: int
    window_seconds: float

class RuntimeStatus(BaseModel):
    provider: str
    workflow: str
    circuit_breaker: CircuitBreakerStatus
    rate_limit: RateLimitStatus

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class MCPAuthType(StrEnum):
    NONE = "none"
    BEARER = "bearer"
    HEADER = "header"


class MCPCapabilityItem(BaseModel):
    name: str
    description: str | None = None


class MCPCapabilities(BaseModel):
    tools: list[MCPCapabilityItem] = Field(default_factory=list)
    resources: list[MCPCapabilityItem] = Field(default_factory=list)
    prompts: list[MCPCapabilityItem] = Field(default_factory=list)


class MCPServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    endpoint: str = Field(min_length=1, max_length=2000)
    auth_type: MCPAuthType = MCPAuthType.NONE
    header_name: str | None = Field(default=None, max_length=200)
    secret_value: str | None = Field(default=None, max_length=4000)
    timeout_seconds: float = Field(default=15.0, gt=0, le=120)
    enabled: bool = True


class MCPServerPublic(BaseModel):
    """Redacted view returned to the frontend — secret_value is never included."""

    id: str
    name: str
    endpoint: str
    auth_type: MCPAuthType
    header_name: str | None = None
    has_secret: bool = False
    timeout_seconds: float
    enabled: bool
    created_at: str
    connected: bool | None = None
    last_check: str | None = None
    last_check_latency_ms: float | None = None
    last_check_error: str | None = None
    capabilities: MCPCapabilities = Field(default_factory=MCPCapabilities)


@dataclass(slots=True)
class MCPServerRecord:
    """Server-side record — the only place secret_value is ever held."""

    id: str
    name: str
    endpoint: str
    auth_type: MCPAuthType
    header_name: str | None
    secret_value: str | None
    timeout_seconds: float
    enabled: bool
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    connected: bool | None = None
    last_check: str | None = None
    last_check_latency_ms: float | None = None
    last_check_error: str | None = None
    capabilities: MCPCapabilities = field(default_factory=MCPCapabilities)

    @classmethod
    def from_create(cls, payload: MCPServerCreate) -> "MCPServerRecord":
        return cls(
            id=str(uuid4()),
            name=payload.name,
            endpoint=payload.endpoint,
            auth_type=payload.auth_type,
            header_name=payload.header_name,
            secret_value=payload.secret_value,
            timeout_seconds=payload.timeout_seconds,
            enabled=payload.enabled,
        )

    def to_public(self) -> MCPServerPublic:
        return MCPServerPublic(
            id=self.id,
            name=self.name,
            endpoint=self.endpoint,
            auth_type=self.auth_type,
            header_name=self.header_name,
            has_secret=bool(self.secret_value),
            timeout_seconds=self.timeout_seconds,
            enabled=self.enabled,
            created_at=self.created_at,
            connected=self.connected,
            last_check=self.last_check,
            last_check_latency_ms=self.last_check_latency_ms,
            last_check_error=self.last_check_error,
            capabilities=self.capabilities,
        )

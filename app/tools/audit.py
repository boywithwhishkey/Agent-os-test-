from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.tenant import get_current_tenant


@dataclass(slots=True)
class ToolAuditEvent:
    timestamp: str
    tool: str
    success: bool
    risk: str
    approval_required: bool
    error: str | None = None
    # Ties an audited execution back to the originating HTTP request. Optional:
    # executions outside a request (background jobs, tests) genuinely have none.
    correlation_id: str | None = None


class ToolAuditLog(ABC):
    @abstractmethod
    async def record(
        self,
        *,
        tool: str,
        success: bool,
        risk: str,
        approval_required: bool,
        error: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class InMemoryToolAuditLog(ToolAuditLog):
    def __init__(self, max_events: int = 1000, *, tenant_id: str = "operator") -> None:
        self.max_events = max_events
        self._tenant_id = tenant_id
        self._events: list[tuple[str, ToolAuditEvent]] = []

    async def record(
        self,
        *,
        tool: str,
        success: bool,
        risk: str,
        approval_required: bool,
        error: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self._events.append(
            (
                get_current_tenant(self._tenant_id),
                ToolAuditEvent(
                timestamp=datetime.now(UTC).isoformat(),
                tool=tool,
                success=success,
                risk=risk,
                approval_required=approval_required,
                error=error,
                correlation_id=correlation_id,
                ),
            )
        )
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events :]

    async def list(self) -> list[dict[str, Any]]:
        tenant_id = get_current_tenant(self._tenant_id)
        return [asdict(event) for event_tenant, event in self._events if event_tenant == tenant_id]

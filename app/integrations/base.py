from __future__ import annotations

from abc import ABC, abstractmethod

from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class IntegrationAdapter(ABC):
    @abstractmethod
    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        raise NotImplementedError

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        """Probe whether the external service is reachable.

        Returns (connected, latency_ms, error). Adapters override this with a
        real network probe; the default reports "unknown" rather than a fake
        success.
        """
        return False, None, "Connection test is not supported for this provider"


def unsupported_execute_result(
    provider: IntegrationProvider, request: IntegrationRequest, *, reason: str
) -> IntegrationResult:
    """Shared response for adapters that only support a connection test, not
    the generic webhook-style execute() (e.g. a database, queue, or an AI/API
    provider verified by a read-only capability check rather than a triggered
    workflow)."""
    return IntegrationResult(
        provider=provider,
        workflow=request.workflow,
        success=False,
        error=reason,
        correlation_id=request.correlation_id,
    )

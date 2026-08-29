from __future__ import annotations

from abc import ABC, abstractmethod

from app.integrations.models import IntegrationRequest, IntegrationResult


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

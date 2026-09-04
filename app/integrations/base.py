from __future__ import annotations

from abc import ABC, abstractmethod

from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class CapabilityNotWired(NotImplementedError):
    """This adapter has no operation for that canonical capability.

    Distinct from a provider failure: nothing was attempted, nothing broke, and
    the honest answer is "not built yet" rather than "the call failed".
    """


class IntegrationAdapter(ABC):
    @abstractmethod
    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        raise NotImplementedError

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        """Perform one canonical capability.

        Adapters override this for the capabilities they actually implement.
        The default refuses rather than returning a plausible-looking empty
        result — a connector reporting success for something it never did is
        the worst outcome available here.

        Called only by the Connector Broker, and only after risk classification
        and the approval gate have passed. An adapter must not re-decide policy
        here, and must not accept a provider endpoint from `arguments`.
        """
        raise CapabilityNotWired(
            f"{type(self).__name__} has no operation for {capability_id}"
        )

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

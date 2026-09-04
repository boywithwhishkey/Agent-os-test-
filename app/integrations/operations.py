"""Default capability execution for the Connector Broker.

Separates *how* a capability reaches a provider from *whether* it is allowed
to. The broker owns risk, approval and audit; this owns adapter construction
and dispatch, and nothing else. It is injected into the broker rather than
imported by it so the governance path stays testable without any provider.
"""

from __future__ import annotations

from app.integrations.base import CapabilityNotWired
from app.integrations.capabilities import Capability
from app.integrations.factory import build_integration_adapter


async def default_perform(connector: str, capability: Capability, arguments: dict) -> object:
    """Build the connector's adapter and run one capability on it.

    Raises `CapabilityNotWired` when the adapter has no operation for it, which
    the broker turns into an honest "not built yet" rather than a failure —
    nothing was attempted and nothing broke.

    `arguments` is passed straight through to the adapter. It carries operation
    parameters only: a provider endpoint must never arrive this way, or the
    capability model stops constraining what an agent can reach.
    """
    adapter = build_integration_adapter(connector)
    return await adapter.run_capability(capability.id, arguments)


__all__ = ["CapabilityNotWired", "default_perform"]

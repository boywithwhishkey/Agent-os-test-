"""The Connector Broker: capability in, provider call out.

Until now the canonical capability layer was declarative. The catalog knew that
Gmail would offer `mail.message.send` and that it is HIGH_RISK, the UI showed
it, and nothing could execute it. An agent still had to name a provider and an
endpoint, which is precisely what the capability model exists to stop.

This is the missing hop:

    capability id -> risk -> policy/approval -> connector -> adapter -> audit

Everything an agent asks for goes through `execute`. It never takes a provider
name from the caller: the broker resolves which connector serves a capability,
so swapping Gmail for Outlook is a routing change rather than a rewrite of
whatever asked for `mail.message.send`.

Four refusals matter more than the success path, and each is a distinct,
audited outcome rather than a generic error:

- **UNKNOWN_CAPABILITY** — the id is not canonical. Never falls through to a
  provider, and never inherits the READ path by default.
- **NO_PROVIDER** — canonical, but nothing in this deployment implements it.
  Declaring a capability in the catalog says what connecting *would* authorise;
  it is not a promise that code exists.
- **NOT_CONNECTED** — a connector exists but has no working credential. This is
  the honest answer to "why did nothing happen", and it names the missing
  environment variables rather than saying "failed".
- **APPROVAL_REQUIRED** — the capability is not READ and no valid approval was
  presented. Decided by `ToolPolicy`, the same component that gates tools, so a
  connector cannot reach a consequential action by a softer path than a tool.

Every outcome is audited, including the refusals. An action that was blocked is
exactly the kind of thing someone needs to find later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.integrations.capabilities import Capability, UnknownCapability, resolve
from app.integrations.catalog import list_catalog
from app.integrations.factory import (
    is_provider_configured,
    list_providers,
    provider_requirements,
)
from app.integrations.models import ConnectorKind
from app.tools.audit import ToolAuditLog
from app.tools.models import ToolRisk
from app.tools.policy import ToolPolicy


class BrokerOutcome(StrEnum):
    OK = "ok"
    UNKNOWN_CAPABILITY = "unknown_capability"
    NO_PROVIDER = "no_provider"
    NOT_CONNECTED = "not_connected"
    APPROVAL_REQUIRED = "approval_required"
    PROVIDER_ERROR = "provider_error"


@dataclass(slots=True)
class BrokerResult:
    outcome: BrokerOutcome
    capability: str
    #: The connector actually selected, when one was. Reported so an audit
    #: reader can see which provider served a capability, but never taken from
    #: the caller.
    connector: str | None = None
    risk: ToolRisk | None = None
    output: object = None
    error: str | None = None
    #: Environment variable NAMES a connector is waiting on. Names only —
    #: values are never read here, let alone returned.
    missing_configuration: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.outcome is BrokerOutcome.OK


def providers_for(capability_id: str) -> list[str]:
    """Connector ids that declare this capability and have an adapter.

    Ordered: connectors that are configured come first, so the broker picks
    something that can actually work rather than the first alphabetically.
    System infrastructure is excluded — PostgreSQL and Redis are the running
    system, not a provider an agent routes user work to.
    """
    candidates = [
        spec.id
        for spec in list_catalog()
        if spec.implemented
        and spec.kind is not ConnectorKind.SYSTEM_INFRASTRUCTURE
        and capability_id in spec.canonical_capabilities
    ]
    return sorted(candidates, key=lambda cid: (not _configured(cid), cid))


def _configured(connector_id: str) -> bool:
    for provider in list_providers():
        if provider.value == connector_id:
            return is_provider_configured(provider)
    return False


def _requirements(connector_id: str) -> list[str]:
    for provider in list_providers():
        if provider.value == connector_id:
            return provider_requirements(provider)
    return []


class ConnectorBroker:
    """Routes a canonical capability to a connector under policy and audit.

    `perform` is injected rather than hardcoded so the broker can be tested
    without a provider, and so the eventual per-capability adapter methods can
    be added without touching the governance path. It is called only after the
    capability is known, a connector is selected, the connector is configured,
    and policy has allowed the action — in that order.
    """

    def __init__(
        self,
        *,
        policy: ToolPolicy,
        audit: ToolAuditLog,
        perform=None,
    ) -> None:
        self.policy = policy
        self.audit = audit
        self._perform = perform

    async def execute(
        self,
        capability_id: str,
        arguments: dict | None = None,
        *,
        approval_id: str | None = None,
        correlation_id: str | None = None,
    ) -> BrokerResult:
        try:
            capability = resolve(capability_id)
        except UnknownCapability:
            # Never guess a risk for an id we do not know. Treated as the
            # highest risk purely so the audit record is not misleading; it is
            # refused either way.
            result = BrokerResult(
                outcome=BrokerOutcome.UNKNOWN_CAPABILITY,
                capability=capability_id,
                risk=ToolRisk.HIGH_RISK,
                error=f"Unknown capability: {capability_id}",
            )
            await self._record(result, correlation_id)
            return result

        providers = providers_for(capability_id)
        if not providers:
            result = BrokerResult(
                outcome=BrokerOutcome.NO_PROVIDER,
                capability=capability_id,
                risk=capability.risk,
                error=(
                    f"No connector in this deployment implements {capability_id}. "
                    "A catalog entry declaring it is not an implementation."
                ),
            )
            await self._record(result, correlation_id)
            return result

        connector = providers[0]
        if not _configured(connector):
            missing = _requirements(connector)
            result = BrokerResult(
                outcome=BrokerOutcome.NOT_CONNECTED,
                capability=capability_id,
                connector=connector,
                risk=capability.risk,
                missing_configuration=missing,
                error=(
                    f"{connector} is not configured"
                    + (f". Set {', '.join(missing)}." if missing else ".")
                ),
            )
            await self._record(result, correlation_id)
            return result

        decision = await self.policy.authorize(
            tool_name=capability_id,
            risk=capability.risk,
            approval_id=approval_id,
        )
        if not decision.allowed:
            result = BrokerResult(
                outcome=BrokerOutcome.APPROVAL_REQUIRED,
                capability=capability_id,
                connector=connector,
                risk=capability.risk,
                error=decision.error,
            )
            await self._record(result, correlation_id, approval_required=True)
            return result

        return await self._invoke(capability, connector, arguments or {}, correlation_id)

    async def _invoke(
        self,
        capability: Capability,
        connector: str,
        arguments: dict,
        correlation_id: str | None,
    ) -> BrokerResult:
        if self._perform is None:
            result = BrokerResult(
                outcome=BrokerOutcome.NO_PROVIDER,
                capability=capability.id,
                connector=connector,
                risk=capability.risk,
                error=(
                    f"{connector} has no operation wired for {capability.id} yet. "
                    "Its adapter currently only verifies the connection."
                ),
            )
            await self._record(result, correlation_id)
            return result

        try:
            output = await self._perform(connector, capability, arguments)
            result = BrokerResult(
                outcome=BrokerOutcome.OK,
                capability=capability.id,
                connector=connector,
                risk=capability.risk,
                output=output,
            )
        # Deliberately broad, for the same reason ToolExecutor is: an
        # unexpected provider failure must become an audited failure, never an
        # unaudited traceback escaping to the caller.
        except Exception as exc:  # noqa: BLE001
            result = BrokerResult(
                outcome=BrokerOutcome.PROVIDER_ERROR,
                capability=capability.id,
                connector=connector,
                risk=capability.risk,
                error=f"{type(exc).__name__}: {exc}",
            )

        await self._record(result, correlation_id)
        return result

    async def _record(
        self,
        result: BrokerResult,
        correlation_id: str | None,
        *,
        approval_required: bool = False,
    ) -> None:
        """Audit every outcome, refusals included.

        The audit row is keyed by the CAPABILITY, not the provider endpoint —
        that is what a workflow references and what someone searches for later.
        The selected connector rides along in the error/output, never a secret.
        """
        await self.audit.record(
            tool=result.capability,
            success=result.success,
            risk=(result.risk or ToolRisk.HIGH_RISK).value,
            approval_required=approval_required,
            error=result.error,
            correlation_id=correlation_id,
        )

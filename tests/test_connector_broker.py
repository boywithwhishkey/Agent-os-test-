"""The Connector Broker's refusals.

The success path is the least interesting thing here. What matters is that
every way of NOT doing something is a distinct, audited outcome — because the
alternative is an agent silently doing nothing, or worse, silently doing
something consequential.
"""

from __future__ import annotations

import asyncio

import pytest

from app.core.tenant import current_tenant_id
from app.integrations.broker import BrokerOutcome, ConnectorBroker, providers_for
from app.integrations.catalog import list_catalog
from app.integrations.models import ConnectorKind
from app.integrations.oauth.store import OAuthConnectionStore
from app.runtime.circuit_breaker import CircuitBreaker
from app.runtime.rate_limit import SlidingWindowRateLimiter
from app.tools.approvals import InMemoryApprovalStore
from app.tools.models import ToolRisk
from app.tools.policy import ToolPolicy

pytestmark = pytest.mark.asyncio


class RecordingAudit:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    async def record(self, **kwargs) -> None:
        self.rows.append(kwargs)


def _broker(perform=None, approvals=None, **controls) -> tuple[ConnectorBroker, RecordingAudit]:
    audit = RecordingAudit()
    broker = ConnectorBroker(
        policy=ToolPolicy(approvals or InMemoryApprovalStore()),
        audit=audit,
        perform=perform,
        **controls,
    )
    return broker, audit


async def test_an_unknown_capability_is_refused_and_never_reaches_a_provider() -> None:
    called = False

    async def perform(*_args):
        nonlocal called
        called = True

    broker, audit = _broker(perform)
    result = await broker.execute("mail.message.exfiltrate")

    assert result.outcome is BrokerOutcome.UNKNOWN_CAPABILITY
    assert called is False
    # Refusals are audited too — a blocked action is exactly what someone
    # searches for afterwards.
    assert audit.rows and audit.rows[0]["success"] is False


async def test_a_declared_but_unwired_capability_never_reports_success() -> None:
    # Gmail declares send, but this first adapter batch only wires read paths.
    broker, _ = _broker()
    result = await broker.execute("mail.message.send", approval_id=None)

    assert result.outcome in {
        BrokerOutcome.NO_PROVIDER,
        BrokerOutcome.NOT_CONNECTED,
        BrokerOutcome.APPROVAL_REQUIRED,
    }
    assert result.success is False


async def test_high_risk_capabilities_are_refused_without_an_approval() -> None:
    called = False

    async def perform(*_args):
        nonlocal called
        called = True
        return {"ok": True}

    broker, audit = _broker(perform)
    # n8n/make implement automation.workflow.trigger, which is HIGH_RISK.
    result = await broker.execute("automation.workflow.trigger")

    assert result.outcome in {BrokerOutcome.APPROVAL_REQUIRED, BrokerOutcome.NOT_CONNECTED}
    assert called is False, "a high-risk capability reached a provider without approval"
    assert audit.rows[-1]["success"] is False


async def test_an_unconfigured_connector_names_the_missing_variables() -> None:
    """"Not connected" must be actionable, not just a failure.

    Naming the environment variable is the difference between a user fixing it
    and filing a bug. Names only — this never reads a value.
    """
    broker, _ = _broker()
    result = await broker.execute("ai.model.list")

    if result.outcome is BrokerOutcome.NOT_CONNECTED:
        assert result.missing_configuration, "did not say what is missing"
        assert all("KEY" in name or "URL" in name or "TOKEN" in name for name in result.missing_configuration)
        # And it must not have leaked whatever the value would be.
        assert all("=" not in name for name in result.missing_configuration)


async def test_a_read_capability_needs_no_approval_and_reaches_the_provider(monkeypatch) -> None:
    seen: dict = {}

    async def perform(connector, capability, arguments):
        seen["connector"] = connector
        seen["capability"] = capability.id
        return {"models": ["a", "b"]}

    # ai.model.list is READ. Pretend the provider is configured so the routing
    # path is exercised rather than short-circuited by a missing key.
    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, audit = _broker(perform)
    result = await broker.execute("ai.model.list", correlation_id="corr-1")

    assert result.outcome is BrokerOutcome.OK
    assert result.risk is ToolRisk.READ
    assert seen["capability"] == "ai.model.list"
    # The broker chose the connector; the caller never named one.
    assert result.connector == seen["connector"]
    assert audit.rows[-1]["correlation_id"] == "corr-1"
    assert audit.rows[-1]["tool"] == "ai.model.list"


async def test_a_provider_exception_becomes_an_audited_failure_not_a_traceback(monkeypatch) -> None:
    async def perform(*_args):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, audit = _broker(perform)
    result = await broker.execute("ai.model.list")

    assert result.outcome is BrokerOutcome.PROVIDER_ERROR
    assert "provider exploded" in result.error
    assert audit.rows[-1]["success"] is False


async def test_broker_rate_limit_is_enforced_and_audited(monkeypatch) -> None:
    calls = 0

    async def perform(*_args):
        nonlocal calls
        calls += 1
        return {"ok": True}

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, audit = _broker(
        perform,
        rate_limiter=SlidingWindowRateLimiter(limit=1, window_seconds=60),
    )

    first = await broker.execute("ai.model.list")
    second = await broker.execute("ai.model.list")

    assert first.outcome is BrokerOutcome.OK
    assert second.outcome is BrokerOutcome.RATE_LIMITED
    assert calls == 1
    assert audit.rows[-1]["success"] is False


async def test_broker_runtime_controls_are_tenant_isolated(monkeypatch) -> None:
    async def perform(*_args):
        return {"ok": True}

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, _ = _broker(
        perform,
        rate_limiter=SlidingWindowRateLimiter(limit=1, window_seconds=60),
    )

    tenant_a = current_tenant_id.set("tenant-a")
    try:
        first_a = await broker.execute("ai.model.list")
    finally:
        current_tenant_id.reset(tenant_a)
    tenant_b = current_tenant_id.set("tenant-b")
    try:
        first_b = await broker.execute("ai.model.list")
    finally:
        current_tenant_id.reset(tenant_b)
    tenant_a_again = current_tenant_id.set("tenant-a")
    try:
        second_a = await broker.execute("ai.model.list")
    finally:
        current_tenant_id.reset(tenant_a_again)

    assert first_a.outcome is BrokerOutcome.OK
    assert first_b.outcome is BrokerOutcome.OK
    assert second_a.outcome is BrokerOutcome.RATE_LIMITED


async def test_broker_circuit_breaker_is_scoped_and_stops_repeated_failures(monkeypatch) -> None:
    calls = 0

    async def perform(*_args):
        nonlocal calls
        calls += 1
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, audit = _broker(
        perform,
        circuit_breaker=CircuitBreaker(failure_threshold=1, recovery_seconds=60),
    )

    first = await broker.execute("ai.model.list")
    second = await broker.execute("ai.model.list")

    assert first.outcome is BrokerOutcome.PROVIDER_ERROR
    assert second.outcome is BrokerOutcome.CIRCUIT_OPEN
    assert calls == 1
    assert audit.rows[-1]["success"] is False


async def test_broker_retries_provider_failures_before_auditing_success(monkeypatch) -> None:
    calls = 0

    async def perform(*_args):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary provider failure")
        return {"ok": True}

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, _ = _broker(perform, max_retries=1, backoff_base_seconds=0)

    result = await broker.execute("ai.model.list")

    assert result.outcome is BrokerOutcome.OK
    assert result.output == {"ok": True}
    assert calls == 2


async def test_broker_times_out_a_provider_call(monkeypatch) -> None:
    async def perform(*_args):
        await asyncio.sleep(0.05)
        return {"ok": True}

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, _ = _broker(perform, timeout_seconds=0.001)

    result = await broker.execute("ai.model.list")

    assert result.outcome is BrokerOutcome.PROVIDER_ERROR
    assert "timed out" in (result.error or "")


async def test_configured_oauth_app_without_account_is_explicitly_not_connected(monkeypatch) -> None:
    called = False

    async def perform(*_args):
        nonlocal called
        called = True

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: cid == "gmail")
    monkeypatch.setattr("app.integrations.broker.oauth_connection_store", OAuthConnectionStore())
    broker, audit = _broker(perform)

    result = await broker.execute("mail.message.list", correlation_id="oauth-missing")

    assert result.outcome is BrokerOutcome.NOT_CONNECTED
    assert result.connector == "gmail"
    assert "Authorize" in (result.error or "")
    assert called is False
    assert audit.rows[-1]["correlation_id"] == "oauth-missing"
    assert audit.rows[-1]["success"] is False


async def test_connected_provider_wins_over_configured_oauth_app_without_account(monkeypatch) -> None:
    """A disconnected OAuth app must not shadow a ready sibling connector."""

    async def perform(connector, capability, arguments):
        assert capability.id == "chat.message.send"
        return {"connector": connector, "ok": True}

    configured = {"slack", "telegram"}
    monkeypatch.setattr(
        "app.integrations.broker._configured",
        lambda connector_id: connector_id in configured,
    )
    monkeypatch.setattr(
        "app.integrations.broker._oauth_connection_missing",
        lambda connector_id: connector_id == "slack",
    )
    approvals = InMemoryApprovalStore()
    grant = await approvals.issue("chat.message.send", "operator", "test")
    broker, audit = _broker(perform, approvals)

    result = await broker.execute(
        "chat.message.send",
        arguments={"text": "hello"},
        approval_id=grant.approval_id,
    )

    assert result.outcome is BrokerOutcome.OK
    assert result.connector == "telegram"
    assert result.output == {"connector": "telegram", "ok": True}
    assert audit.rows[-1]["success"] is True


async def test_a_capability_with_no_wired_operation_is_honest_about_it(monkeypatch) -> None:
    # Every OAuth adapter today only verifies the connection. Routing must say
    # that, not pretend the call happened.
    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, _ = _broker(perform=None)
    result = await broker.execute("ai.model.list")

    assert result.outcome is BrokerOutcome.NO_PROVIDER
    assert "no operation wired" in result.error


async def test_routing_never_selects_thynacts_own_infrastructure() -> None:
    """PostgreSQL and Redis are the running system, not a provider to route to.

    Without this, `data.record.read` would route user work straight into
    THYNACT's own database.
    """
    infra = {s.id for s in list_catalog() if s.kind is ConnectorKind.SYSTEM_INFRASTRUCTURE}
    assert infra, "no infrastructure entries — this test would pass vacuously"
    for spec in list_catalog():
        for capability_id in spec.canonical_capabilities:
            assert not (set(providers_for(capability_id)) & infra)


async def test_the_caller_cannot_choose_the_provider() -> None:
    """The signature is the guarantee.

    If a provider argument ever appears here, agents will start naming
    providers and the capability model stops being load-bearing.
    """
    import inspect

    params = set(inspect.signature(ConnectorBroker.execute).parameters)
    assert params == {"self", "capability_id", "arguments", "approval_id", "correlation_id"}


async def test_a_wired_capability_runs_end_to_end_through_the_governed_path(monkeypatch) -> None:
    """The whole chain on one real operation: `ai.model.list` on OpenAI.

    Capability -> risk -> policy -> connector selection -> adapter -> audit,
    with the provider's HTTP call stubbed. This is IMPLEMENTED_TESTED, not
    LIVE_VALIDATED: no request left this process.
    """
    import httpx

    from app.integrations.capabilities import resolve
    from app.integrations.openai import OpenAIAdapter
    from app.integrations.operations import default_perform

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.openai.com"
        # The key must travel as a header, never in the URL.
        assert request.headers["Authorization"].startswith("Bearer ")
        assert "test-key" not in str(request.url)
        return httpx.Response(
            200, json={"data": [{"id": "gpt-5"}, {"id": "gpt-4o"}]}
        )

    stub = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = OpenAIAdapter(api_key="test-key", client=stub)

    async def perform(connector, capability, arguments):
        assert connector == "openai"
        return await adapter.run_capability(capability.id, arguments)

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: cid == "openai")
    broker, audit = _broker(perform)
    result = await broker.execute("ai.model.list", correlation_id="corr-e2e")
    await stub.aclose()

    assert result.outcome is BrokerOutcome.OK
    assert result.connector == "openai"
    assert result.output == {"models": ["gpt-4o", "gpt-5"]}

    row = audit.rows[-1]
    assert row["tool"] == "ai.model.list"
    assert row["success"] is True
    assert row["risk"] == "read"
    assert row["correlation_id"] == "corr-e2e"
    # The audit trail must never carry the credential.
    assert "test-key" not in str(row)

    # And default_perform is the production wiring for the same path.
    assert default_perform.__module__ == "app.integrations.operations"
    assert resolve("ai.model.list").risk is ToolRisk.READ


async def test_an_adapter_without_the_operation_reports_not_built_not_an_outage(monkeypatch) -> None:
    import httpx

    from app.integrations.openai import OpenAIAdapter

    adapter = OpenAIAdapter(
        api_key="test-key", client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    )

    async def perform(connector, capability, arguments):
        return await adapter.run_capability(capability.id, arguments)

    monkeypatch.setattr("app.integrations.broker._configured", lambda cid: True)
    broker, _ = _broker(perform)
    # OpenAI declares ai.completion.create in the catalog; no operation exists.
    result = await broker.execute("ai.completion.create", approval_id=None)

    # Refused before it ever reaches the adapter (WRITE needs approval), or
    # reported as unwired — never as a provider error.
    assert result.outcome in {BrokerOutcome.APPROVAL_REQUIRED, BrokerOutcome.NO_PROVIDER}
    assert result.outcome is not BrokerOutcome.PROVIDER_ERROR

import asyncio

from fastapi.testclient import TestClient

from app.api import phase9
from app.integrations.broker import BrokerOutcome, BrokerResult
from app.main import app
from app.tools.approvals import InMemoryApprovalStore
from app.tools.models import ToolRisk

client = TestClient(app)
AUTH = {"X-API-Key": "test-api-key"}


def test_capability_execution_requires_operator_authentication():
    response = client.post(
        "/api/v1/integrations/capabilities/execute",
        json={"capability": "ai.model.list"},
    )

    assert response.status_code == 401


def test_capability_execution_routes_only_the_canonical_request(monkeypatch):
    seen: dict[str, object] = {}

    class FakeBroker:
        async def execute(self, capability, arguments, *, approval_id, correlation_id):
            seen.update(
                capability=capability,
                arguments=arguments,
                approval_id=approval_id,
                correlation_id=correlation_id,
            )
            return BrokerResult(
                outcome=BrokerOutcome.OK,
                capability=capability,
                connector="openai",
                risk=ToolRisk.READ,
                output={"models": ["test-model"]},
            )

    monkeypatch.setattr(phase9, "capability_broker", FakeBroker())
    response = client.post(
        "/api/v1/integrations/capabilities/execute",
        headers={**AUTH, "X-Correlation-ID": "cap-api-1"},
        json={
            "capability": "ai.model.list",
            "arguments": {"page_size": 5},
            "approval_id": "unused-for-read",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "outcome": "ok",
        "capability": "ai.model.list",
        "connector": "openai",
        "risk": "read",
        "output": {"models": ["test-model"]},
        "error": None,
        "missing_configuration": [],
        "correlation_id": "cap-api-1",
    }
    assert seen == {
        "capability": "ai.model.list",
        "arguments": {"page_size": 5},
        "approval_id": "unused-for-read",
        "correlation_id": "cap-api-1",
    }


def test_capability_execution_rejects_provider_override():
    response = client.post(
        "/api/v1/integrations/capabilities/execute",
        headers=AUTH,
        json={"capability": "ai.model.list", "provider": "openai"},
    )

    assert response.status_code == 422


def test_capability_approval_is_single_use_and_canonical(monkeypatch):
    approvals = InMemoryApprovalStore()
    monkeypatch.setattr(phase9, "capability_approvals", approvals)

    issued = client.post(
        "/api/v1/integrations/capabilities/approvals",
        headers=AUTH,
        json={
            "capability": "mail.message.send",
            "approved_by": "operator",
            "reason": "test approval",
        },
    )

    assert issued.status_code == 200
    grant = issued.json()
    assert grant["tool"] == "mail.message.send"
    assert asyncio.run(approvals.consume(grant["approval_id"], "mail.message.send")) is not None
    assert asyncio.run(approvals.consume(grant["approval_id"], "mail.message.send")) is None


def test_capability_approval_rejects_unknown_id():
    response = client.post(
        "/api/v1/integrations/capabilities/approvals",
        headers=AUTH,
        json={"capability": "mail.message.exfiltrate", "approved_by": "operator"},
    )

    assert response.status_code == 404

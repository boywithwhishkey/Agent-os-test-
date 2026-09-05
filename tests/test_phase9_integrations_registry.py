import pytest
from fastapi.testclient import TestClient

from app.api import phase9
from app.core.config import settings
from app.main import app

client = TestClient(app)
AUTH = {"X-API-Key": "test-api-key"}


@pytest.fixture(autouse=True)
def _reset_status_store():
    phase9.status_store._records.clear()
    yield
    phase9.status_store._records.clear()


def test_list_integrations_reports_unconfigured_n8n(monkeypatch):
    monkeypatch.setattr(settings, "n8n_base_url", "")

    response = client.get("/api/v1/integrations", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    n8n = next(item for item in body if item["provider"] == "n8n")
    assert n8n["configured"] is False
    assert n8n["requires"] == ["N8N_BASE_URL"]
    assert n8n["connected"] is None


def test_test_connection_rejects_unconfigured_provider(monkeypatch):
    monkeypatch.setattr(settings, "n8n_base_url", "")

    response = client.post("/api/v1/integrations/n8n/test", headers=AUTH)

    assert response.status_code == 503
    assert "N8N_BASE_URL" in response.json()["detail"]


def test_test_connection_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "zapier_webhook_url", "")

    response = client.post("/api/v1/integrations/zapier/test", headers=AUTH)

    assert response.status_code == 503
    assert "ZAPIER_WEBHOOK_URL" in response.json()["detail"]


def test_test_connection_records_success_and_updates_registry(monkeypatch):
    monkeypatch.setattr(settings, "n8n_base_url", "https://n8n.example")

    class FakeAdapter:
        async def test_connection(self):
            return True, 42.5, None

    monkeypatch.setattr(phase9, "build_integration_adapter", lambda provider: FakeAdapter())

    response = client.post("/api/v1/integrations/n8n/test", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["last_check_latency_ms"] == 42.5
    assert body["last_check"] is not None

    listing = client.get("/api/v1/integrations", headers=AUTH).json()
    n8n = next(item for item in listing if item["provider"] == "n8n")
    assert n8n["connected"] is True
    assert n8n["configured"] is True


def test_test_connection_records_failure(monkeypatch):
    monkeypatch.setattr(settings, "n8n_base_url", "https://n8n.example")

    class FakeAdapter:
        async def test_connection(self):
            return False, None, "Connection refused"

    monkeypatch.setattr(phase9, "build_integration_adapter", lambda provider: FakeAdapter())

    response = client.post("/api/v1/integrations/n8n/test", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["last_check_error"] == "Connection refused"


def test_execute_records_last_execution_outcome(monkeypatch):
    monkeypatch.setattr(settings, "n8n_base_url", "https://n8n.example")

    class FakeAdapter:
        async def execute(self, request):
            from app.integrations.models import IntegrationProvider, IntegrationResult

            return IntegrationResult(
                provider=IntegrationProvider.N8N,
                workflow=request.workflow,
                success=True,
                status_code=200,
                data={"ok": True},
            )

    monkeypatch.setattr(phase9, "build_integration_adapter", lambda provider: FakeAdapter())

    response = client.post(
        "/api/v1/integrations/execute",
        headers=AUTH,
        json={"provider": "n8n", "request": {"workflow": "notify"}},
    )
    assert response.status_code == 200

    listing = client.get("/api/v1/integrations", headers=AUTH).json()
    n8n = next(item for item in listing if item["provider"] == "n8n")
    assert n8n["last_execution_success"] is True
    assert n8n["last_execution"] is not None

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


@pytest.mark.parametrize(
    "provider_id,setting_name",
    [
        ("gemini", "gemini_api_key"),
        ("postgresql", "database_url"),
        ("redis", "redis_url"),
        ("openai", "openai_api_key"),
        ("anthropic", "anthropic_api_key"),
        ("cloudflare", "cloudflare_api_token"),
        ("render", "render_api_key"),
    ],
)
def test_test_connection_no_longer_404s_for_implemented_connectors(monkeypatch, provider_id, setting_name):
    """Regression test: these connectors are implemented=True in the catalog
    and their UI shows an enabled "Test connection" button, but before this
    fix `list_providers()` only contained n8n, so clicking Test on any other
    implemented connector 404'd."""
    monkeypatch.setattr(settings, setting_name, "configured-value")

    class FakeAdapter:
        async def test_connection(self):
            return True, 5.0, None

    monkeypatch.setattr(phase9, "build_integration_adapter", lambda provider: FakeAdapter())

    response = client.post(f"/api/v1/integrations/{provider_id}/test", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["connected"] is True


def test_unconfigured_new_provider_rejects_test_with_clear_message(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)

    response = client.post("/api/v1/integrations/openai/test", headers=AUTH)

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_catalog_reflects_real_test_result_for_openai(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")

    class FakeAdapter:
        async def test_connection(self):
            return True, 12.0, None

    monkeypatch.setattr(phase9, "build_integration_adapter", lambda provider: FakeAdapter())
    client.post("/api/v1/integrations/openai/test", headers=AUTH)

    listing = client.get("/api/v1/integrations").json()
    openai_entry = next(item for item in listing if item["id"] == "openai")
    assert openai_entry["status"] == "connected"
    assert openai_entry["connected"] is True
    assert openai_entry["last_check_latency_ms"] == 12.0


def test_catalog_reflects_failed_test_result_for_cloudflare(monkeypatch):
    monkeypatch.setattr(settings, "cloudflare_api_token", "cf-test")

    class FakeAdapter:
        async def test_connection(self):
            return False, None, "Cloudflare rejected the API token (HTTP 401)"

    monkeypatch.setattr(phase9, "build_integration_adapter", lambda provider: FakeAdapter())
    client.post("/api/v1/integrations/cloudflare/test", headers=AUTH)

    listing = client.get("/api/v1/integrations").json()
    entry = next(item for item in listing if item["id"] == "cloudflare")
    assert entry["status"] == "error"
    assert entry["connected"] is False
    assert "401" in entry["last_check_error"]


def test_catalog_shows_configured_before_any_test_has_run(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-test")

    listing = client.get("/api/v1/integrations").json()
    entry = next(item for item in listing if item["id"] == "anthropic")
    assert entry["status"] == "configured"
    assert entry["connected"] is None

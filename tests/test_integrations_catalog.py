from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_catalog_is_public_no_api_key_required(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "test-api-key")

    response = client.get("/api/v1/integrations")

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 25
    ids = {item["id"] for item in body}
    assert "n8n" in ids
    assert "github" in ids
    assert "postgresql" in ids


def test_catalog_only_entries_are_always_available_and_unimplemented():
    response = client.get("/api/v1/integrations")

    body = response.json()
    github = next(item for item in body if item["id"] == "github")
    assert github["implemented"] is False
    assert github["status"] == "available"
    assert github["configured"] is False
    assert github["connected"] is None


def test_n8n_reflects_real_configuration_state(monkeypatch):
    monkeypatch.setattr(settings, "n8n_base_url", "")

    response = client.get("/api/v1/integrations")

    n8n = next(item for item in response.json() if item["id"] == "n8n")
    assert n8n["implemented"] is True
    assert n8n["status"] == "needs_setup"
    assert n8n["configured"] is False
    assert n8n["requires"] == ["N8N_BASE_URL"]


def test_gemini_reflects_active_llm_provider(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    response = client.get("/api/v1/integrations")
    gemini = next(item for item in response.json() if item["id"] == "gemini")
    assert gemini["status"] == "needs_setup"

    monkeypatch.setattr(settings, "gemini_api_key", "some-key")
    response = client.get("/api/v1/integrations")
    gemini = next(item for item in response.json() if item["id"] == "gemini")
    assert gemini["status"] == "configured"

    monkeypatch.setattr(settings, "llm_provider", "gemini")
    response = client.get("/api/v1/integrations")
    gemini = next(item for item in response.json() if item["id"] == "gemini")
    assert gemini["status"] == "connected"


def test_postgresql_reflects_real_backend_settings(monkeypatch):
    monkeypatch.setattr(settings, "database_url", "")
    monkeypatch.setattr(settings, "memory_backend", "memory")
    monkeypatch.setattr(settings, "task_backend", "memory")
    monkeypatch.setattr(settings, "workflow_backend", "memory")
    monkeypatch.setattr(settings, "runtime_backend", "memory")
    monkeypatch.setattr(settings, "tool_backend", "memory")
    monkeypatch.setattr(settings, "workflow_definition_backend", "memory")
    response = client.get("/api/v1/integrations")
    pg = next(item for item in response.json() if item["id"] == "postgresql")
    assert pg["status"] == "needs_setup"

    monkeypatch.setattr(settings, "database_url", "postgres://example")
    response = client.get("/api/v1/integrations")
    pg = next(item for item in response.json() if item["id"] == "postgresql")
    assert pg["status"] == "configured"

    monkeypatch.setattr(settings, "task_backend", "postgres")
    response = client.get("/api/v1/integrations")
    pg = next(item for item in response.json() if item["id"] == "postgresql")
    assert pg["status"] == "connected"


def test_redis_reflects_real_queue_backend(monkeypatch):
    monkeypatch.setattr(settings, "redis_url", "")
    monkeypatch.setattr(settings, "queue_backend", "memory")
    response = client.get("/api/v1/integrations")
    redis = next(item for item in response.json() if item["id"] == "redis")
    assert redis["status"] == "needs_setup"

    monkeypatch.setattr(settings, "queue_backend", "redis")
    monkeypatch.setattr(settings, "redis_url", "redis://example")
    response = client.get("/api/v1/integrations")
    redis = next(item for item in response.json() if item["id"] == "redis")
    assert redis["status"] == "connected"


def test_every_catalog_entry_has_required_metadata():
    response = client.get("/api/v1/integrations")
    for item in response.json():
        assert item["id"]
        assert item["name"]
        assert item["description"]
        assert item["category"]
        assert item["connector_type"] in {"mcp", "api", "oauth", "webhook"}
        assert item["auth_type"]
        assert isinstance(item["capabilities"], list)

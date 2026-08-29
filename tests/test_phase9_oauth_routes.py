import pytest
from fastapi.testclient import TestClient

from app.api import phase9
from app.core.config import settings
from app.integrations.oauth.registry import oauth_connection_store, oauth_state_store
from app.integrations.oauth.service import OAuthExchangeError
from app.main import app

client = TestClient(app)
AUTH = {"X-API-Key": "test-api-key"}


@pytest.fixture(autouse=True)
def _reset_oauth_state():
    oauth_state_store._states.clear()
    oauth_connection_store._connections.clear()
    phase9.status_store._records.clear()
    yield
    oauth_state_store._states.clear()
    oauth_connection_store._connections.clear()
    phase9.status_store._records.clear()


def test_authorize_requires_operator_auth():
    response = client.get("/api/v1/integrations/oauth/github/authorize")
    assert response.status_code in (401, 503)


def test_authorize_rejects_unknown_provider():
    response = client.get("/api/v1/integrations/oauth/not-a-real-provider/authorize", headers=AUTH)
    assert response.status_code == 404


def test_authorize_reports_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", None)

    response = client.get("/api/v1/integrations/oauth/github/authorize", headers=AUTH)

    assert response.status_code == 503
    assert "GITHUB_OAUTH_CLIENT_ID" in response.json()["detail"]


def test_authorize_returns_url_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")

    response = client.get("/api/v1/integrations/oauth/github/authorize", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["authorize_url"].startswith("https://github.com/login/oauth/authorize?")


def test_callback_rejects_missing_or_reused_state():
    response = client.get("/api/v1/integrations/oauth/github/callback?code=abc&state=nonexistent", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "invalid_or_expired_state" in response.headers["location"]


def test_callback_surfaces_provider_denial():
    state = oauth_state_store.create("github")
    response = client.get(
        f"/api/v1/integrations/oauth/github/callback?state={state}&error=access_denied", follow_redirects=False
    )
    assert "error=access_denied" in response.headers["location"] or "message=access_denied" in response.headers["location"]


def test_callback_exchanges_code_and_records_connection(monkeypatch):
    state = oauth_state_store.create("github")

    async def fake_exchange(config, *, code, connection_store, client=None):
        connection_store.record_success(config.id, access_token="gho_test", token_type="bearer", scope="repo")

    monkeypatch.setattr(phase9, "exchange_code", fake_exchange)

    response = client.get(
        f"/api/v1/integrations/oauth/github/callback?state={state}&code=the-code", follow_redirects=False
    )

    assert response.status_code in (302, 307)
    assert "oauth=connected" in response.headers["location"]
    assert oauth_connection_store.get("github").connected is True


def test_callback_surfaces_exchange_failure(monkeypatch):
    state = oauth_state_store.create("github")

    async def fake_exchange(config, *, code, connection_store, client=None):
        raise OAuthExchangeError("GitHub rejected the authorization code: bad_verification_code")

    monkeypatch.setattr(phase9, "exchange_code", fake_exchange)

    response = client.get(
        f"/api/v1/integrations/oauth/github/callback?state={state}&code=stale", follow_redirects=False
    )

    assert "oauth=error" in response.headers["location"]


def test_catalog_reflects_connected_github_after_oauth(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")
    oauth_connection_store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")

    listing = client.get("/api/v1/integrations").json()
    github = next(item for item in listing if item["id"] == "github")

    assert github["status"] == "connected"
    assert github["configured"] is True


def test_disconnect_requires_auth_and_clears_connection(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")
    oauth_connection_store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")

    unauth = client.delete("/api/v1/integrations/oauth/github")
    assert unauth.status_code in (401, 503)

    response = client.delete("/api/v1/integrations/oauth/github", headers=AUTH)
    assert response.status_code == 204
    assert oauth_connection_store.get("github").connected is False

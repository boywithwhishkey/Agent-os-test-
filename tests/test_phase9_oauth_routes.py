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


async def test_callback_exchanges_code_and_records_connection(monkeypatch):
    state = oauth_state_store.create("github")

    async def fake_exchange(config, *, code, connection_store, client=None):
        await connection_store.record_success(config.id, access_token="gho_test", token_type="bearer", scope="repo")

    monkeypatch.setattr(phase9, "exchange_code", fake_exchange)

    response = client.get(
        f"/api/v1/integrations/oauth/github/callback?state={state}&code=the-code", follow_redirects=False
    )

    assert response.status_code in (302, 307)
    assert "oauth=connected" in response.headers["location"]
    assert (await oauth_connection_store.get("github")).connected is True


def test_callback_surfaces_exchange_failure(monkeypatch):
    state = oauth_state_store.create("github")

    async def fake_exchange(config, *, code, connection_store, client=None):
        raise OAuthExchangeError("GitHub rejected the authorization code: bad_verification_code")

    monkeypatch.setattr(phase9, "exchange_code", fake_exchange)

    response = client.get(
        f"/api/v1/integrations/oauth/github/callback?state={state}&code=stale", follow_redirects=False
    )

    assert "oauth=error" in response.headers["location"]


async def test_catalog_reflects_connected_github_after_oauth(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")
    await oauth_connection_store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")

    listing = client.get("/api/v1/integrations").json()
    github = next(item for item in listing if item["id"] == "github")

    assert github["status"] == "connected"
    assert github["configured"] is True


async def test_disconnect_requires_auth_and_clears_connection(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")
    await oauth_connection_store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")

    unauth = client.delete("/api/v1/integrations/oauth/github")
    assert unauth.status_code in (401, 503)

    response = client.delete("/api/v1/integrations/oauth/github", headers=AUTH)
    assert response.status_code == 204
    assert (await oauth_connection_store.get("github")).connected is False


@pytest.mark.parametrize(
    "provider_id,client_id_setting,client_secret_setting,authorize_prefix",
    [
        ("slack", "slack_oauth_client_id", "slack_oauth_client_secret", "https://slack.com/oauth/v2/authorize?"),
        ("notion", "notion_oauth_client_id", "notion_oauth_client_secret", "https://api.notion.com/v1/oauth/authorize?"),
        ("gitlab", "gitlab_oauth_client_id", "gitlab_oauth_client_secret", "https://gitlab.com/oauth/authorize?"),
    ],
)
async def test_generic_oauth_routes_work_for_every_registered_provider(
    monkeypatch, provider_id, client_id_setting, client_secret_setting, authorize_prefix
):
    """The authorize/callback/disconnect routes are provider-agnostic — this
    proves it for Slack/Notion/GitLab, not just the GitHub example above."""
    monkeypatch.setattr(settings, client_id_setting, "client-123")
    monkeypatch.setattr(settings, client_secret_setting, "secret-456")

    authorize = client.get(f"/api/v1/integrations/oauth/{provider_id}/authorize", headers=AUTH)
    assert authorize.status_code == 200
    assert authorize.json()["authorize_url"].startswith(authorize_prefix)

    state = oauth_state_store.create(provider_id)

    async def fake_exchange(config, *, code, connection_store, client=None):
        await connection_store.record_success(config.id, access_token="tok", token_type="bearer", scope=None)

    monkeypatch.setattr(phase9, "exchange_code", fake_exchange)
    callback = client.get(
        f"/api/v1/integrations/oauth/{provider_id}/callback?state={state}&code=the-code", follow_redirects=False
    )
    assert f"provider={provider_id}" in callback.headers["location"]
    assert "oauth=connected" in callback.headers["location"]

    listing = client.get("/api/v1/integrations").json()
    entry = next(item for item in listing if item["id"] == provider_id)
    assert entry["status"] == "connected"

    disconnect = client.delete(f"/api/v1/integrations/oauth/{provider_id}", headers=AUTH)
    assert disconnect.status_code == 204
    assert (await oauth_connection_store.get(provider_id)).connected is False

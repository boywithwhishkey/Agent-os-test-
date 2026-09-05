import base64

import httpx
import pytest

from app.core.config import settings
from app.integrations.oauth import service
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import OAuthExchangeError, OAuthNotConfigured
from app.integrations.oauth.store import OAuthConnectionStore, OAuthStateStore

GITHUB = OAUTH_PROVIDERS["github"]
SLACK = OAUTH_PROVIDERS["slack"]
NOTION = OAUTH_PROVIDERS["notion"]
GITLAB = OAUTH_PROVIDERS["gitlab"]


def test_build_authorize_url_includes_state_and_redirect(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "oauth_redirect_base_url", "https://api.example.com")
    state_store = OAuthStateStore()

    url = service.build_authorize_url(GITHUB, state_store)

    assert url.startswith("https://github.com/login/oauth/authorize?")
    assert "client_id=client-123" in url
    assert "redirect_uri=https%3A%2F%2Fapi.example.com%2Fapi%2Fv1%2Fintegrations%2Foauth%2Fgithub%2Fcallback" in url
    assert "state=" in url


def test_build_authorize_url_requires_client_id(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", None)
    with pytest.raises(OAuthNotConfigured):
        service.build_authorize_url(GITHUB, OAuthStateStore())


def test_state_store_is_single_use():
    store = OAuthStateStore()
    state = store.create("github")

    assert store.consume(state) == "github"
    assert store.consume(state) is None


@pytest.mark.asyncio
async def test_exchange_code_success(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Accept"] == "application/json"
        return httpx.Response(200, json={"access_token": "gho_abc", "token_type": "bearer", "scope": "repo"})

    connection_store = OAuthConnectionStore()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await service.exchange_code(GITHUB, code="the-code", connection_store=connection_store, client=client)

    record = connection_store.get("github")
    assert record.connected is True
    assert record.access_token == "gho_abc"


@pytest.mark.asyncio
async def test_exchange_code_preserves_existing_refresh_token_when_provider_omits_it(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "gho_rotated", "token_type": "bearer"})

    connection_store = OAuthConnectionStore()
    connection_store.record_success(
        "github",
        access_token="gho_old",
        refresh_token="refresh-stable",
        token_type="bearer",
        scope="repo",
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await service.exchange_code(GITHUB, code="the-code", connection_store=connection_store, client=client)

    record = connection_store.get("github")
    assert record.access_token == "gho_rotated"
    assert record.refresh_token == "refresh-stable"


@pytest.mark.asyncio
async def test_exchange_code_requires_client_secret(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_secret", None)
    with pytest.raises(OAuthNotConfigured):
        await service.exchange_code(GITHUB, code="x", connection_store=OAuthConnectionStore())


@pytest.mark.asyncio
async def test_exchange_code_rejects_provider_error(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "bad_verification_code", "error_description": "expired code"})

    connection_store = OAuthConnectionStore()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OAuthExchangeError, match="expired code"):
            await service.exchange_code(GITHUB, code="stale", connection_store=connection_store, client=client)

    assert connection_store.get("github").connected is False


@pytest.mark.asyncio
async def test_exchange_code_reports_network_error(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    connection_store = OAuthConnectionStore()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OAuthExchangeError):
            await service.exchange_code(GITHUB, code="x", connection_store=connection_store, client=client)


# --- Slack: same "body" token_auth as GitHub, but always answers HTTP 200 ---


@pytest.mark.asyncio
async def test_slack_exchange_code_detects_ok_false_despite_http_200(monkeypatch):
    monkeypatch.setattr(settings, "slack_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "slack_oauth_client_secret", "secret-456")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "error": "invalid_code"})

    connection_store = OAuthConnectionStore()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OAuthExchangeError, match="invalid_code"):
            await service.exchange_code(SLACK, code="stale", connection_store=connection_store, client=client)


# --- Notion: HTTP Basic auth + JSON body, not form + body credentials ---


def test_notion_authorize_url_includes_owner_param(monkeypatch):
    monkeypatch.setattr(settings, "notion_oauth_client_id", "client-123")
    url = service.build_authorize_url(NOTION, OAuthStateStore())

    assert "owner=user" in url
    assert "scope=" not in url  # Notion has no OAuth scope param


@pytest.mark.asyncio
async def test_notion_exchange_code_uses_basic_auth_and_json_body(monkeypatch):
    monkeypatch.setattr(settings, "notion_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "notion_oauth_client_secret", "secret-456")

    expected_basic = base64.b64encode(b"client-123:secret-456").decode()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == f"Basic {expected_basic}"
        assert request.headers["Content-Type"] == "application/json"
        import json

        body = json.loads(request.content)
        assert body["grant_type"] == "authorization_code"
        assert body["code"] == "the-code"
        assert "client_secret" not in body  # must not leak into the JSON body when using Basic auth
        return httpx.Response(200, json={"access_token": "secret_notion", "token_type": "bearer"})

    connection_store = OAuthConnectionStore()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await service.exchange_code(NOTION, code="the-code", connection_store=connection_store, client=client)

    assert connection_store.get("notion").connected is True


# --- GitLab: standard form/body auth, same as GitHub ---


@pytest.mark.asyncio
async def test_gitlab_exchange_code_success(monkeypatch):
    monkeypatch.setattr(settings, "gitlab_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "gitlab_oauth_client_secret", "secret-456")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "glpat-abc", "token_type": "bearer", "scope": "read_api"})

    connection_store = OAuthConnectionStore()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await service.exchange_code(GITLAB, code="the-code", connection_store=connection_store, client=client)

    assert connection_store.get("gitlab").connected is True

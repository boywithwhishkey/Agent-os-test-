import httpx
import pytest

from app.core.config import settings
from app.integrations.oauth import service
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import OAuthExchangeError, OAuthNotConfigured
from app.integrations.oauth.store import OAuthConnectionStore, OAuthStateStore

GITHUB = OAUTH_PROVIDERS["github"]


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

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.core.auth import require_api_key
from app.core.config import settings
from app.core.correlation import get_or_create_correlation_id
from app.integrations.capabilities import requires_approval, resolve_all
from app.integrations.catalog import CatalogSpec, list_catalog
from app.integrations.factory import (
    build_integration_adapter,
    is_provider_configured,
    list_providers,
    provider_display_name,
    provider_requirements,
)
from app.integrations.mcp.client import MCPHttpClient
from app.integrations.mcp.models import MCPServerCreate, MCPServerPublic
from app.integrations.mcp.store import MCPServerStore
from app.integrations.models import (
    CapabilityDetail,
    ConnectorEntry,
    ConnectorStatusValue,
    IntegrationRequest,
    IntegrationResult,
    IntegrationStatus,
)
from app.integrations.oauth.config import get_oauth_provider
from app.integrations.oauth.models import OAuthAuthorizeResponse
from app.integrations.oauth.registry import oauth_connection_store, oauth_state_store
from app.integrations.oauth.service import (
    OAuthExchangeError,
    OAuthNotConfigured,
    build_authorize_url,
    exchange_code,
)
from app.integrations.status_store import IntegrationStatusStore
from app.integrations.url_guard import UnsafeURLError, validate_outbound_url

public_router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])
router = APIRouter(
    prefix="/api/v1/integrations",
    tags=["integrations"],
    dependencies=[Depends(require_api_key)],
)
status_store = IntegrationStatusStore()
mcp_store = MCPServerStore()


class IntegrationExecutePayload(BaseModel):
    provider: str = Field(default="n8n")
    request: IntegrationRequest


# ---------------------------------------------------------------------------
# Live status resolution for the static catalog. Only entries with
# implemented=True get anything other than AVAILABLE/configured=False —
# see CatalogSpec's module docstring in app/integrations/catalog.py.
# ---------------------------------------------------------------------------


def _status_store_backed_status(provider_id: str, *, configured: bool, force_connected: bool = False) -> dict:
    """Shared status shape for any implemented connector whose only source of
    truth for "connected" is the last real test_connection() call recorded in
    status_store — i.e. every implemented connector except n8n's webhook
    reachability check, which uses this same shape directly.

    `force_connected` additionally reports CONNECTED when the connector is
    known to be in active use right now (e.g. Postgres/Redis already backing
    a live feature) even if no explicit "Test connection" click has happened
    yet this process.
    """
    record = status_store.get(provider_id)
    if not configured:
        status = ConnectorStatusValue.NEEDS_SETUP
    elif record.connected is True or force_connected:
        status = ConnectorStatusValue.CONNECTED
    elif record.connected is False:
        status = ConnectorStatusValue.ERROR
    else:
        status = ConnectorStatusValue.CONFIGURED
    return {
        "status": status,
        "configured": configured,
        "connected": True if force_connected else record.connected,
        "last_check": record.last_check,
        "last_check_latency_ms": record.last_check_latency_ms,
        "last_check_error": record.last_check_error,
        "last_execution": record.last_execution,
        "last_execution_success": record.last_execution_success,
    }


def _n8n_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "n8n")
    return _status_store_backed_status("n8n", configured=is_provider_configured(provider))


def _gemini_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "gemini")
    active = settings.llm_provider.lower().strip() == "gemini"
    return _status_store_backed_status(
        "gemini", configured=is_provider_configured(provider), force_connected=active
    )


def _postgresql_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "postgresql")
    backends = {
        settings.memory_backend,
        settings.task_backend,
        settings.workflow_backend,
        settings.runtime_backend,
        settings.tool_backend,
        settings.workflow_definition_backend,
    }
    in_use = "postgres" in backends
    return _status_store_backed_status(
        "postgresql", configured=is_provider_configured(provider), force_connected=in_use
    )


def _redis_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "redis")
    in_use = settings.queue_backend.lower().strip() == "redis"
    return _status_store_backed_status(
        "redis", configured=is_provider_configured(provider), force_connected=in_use
    )


def _openai_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "openai")
    return _status_store_backed_status("openai", configured=is_provider_configured(provider))


def _anthropic_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "anthropic")
    return _status_store_backed_status("anthropic", configured=is_provider_configured(provider))


def _cloudflare_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "cloudflare")
    return _status_store_backed_status("cloudflare", configured=is_provider_configured(provider))


def _render_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "render")
    return _status_store_backed_status("render", configured=is_provider_configured(provider))


def _make_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "make")
    return _status_store_backed_status("make", configured=is_provider_configured(provider))


def _discord_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "discord")
    return _status_store_backed_status("discord", configured=is_provider_configured(provider))


def _telegram_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "telegram")
    return _status_store_backed_status("telegram", configured=is_provider_configured(provider))


def _whatsapp_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "whatsapp")
    return _status_store_backed_status("whatsapp", configured=is_provider_configured(provider))


def _instagram_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "instagram")
    return _status_store_backed_status("instagram", configured=is_provider_configured(provider))


def _teams_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "teams")
    return _status_store_backed_status("teams", configured=is_provider_configured(provider))


def _shopify_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "shopify")
    return _status_store_backed_status("shopify", configured=is_provider_configured(provider))


def _stripe_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "stripe")
    return _status_store_backed_status("stripe", configured=is_provider_configured(provider))


def _snapchat_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "snapchat")
    return _status_store_backed_status("snapchat", configured=is_provider_configured(provider))


def _woocommerce_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "woocommerce")
    return _status_store_backed_status("woocommerce", configured=is_provider_configured(provider))


def _vercel_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "vercel")
    return _status_store_backed_status("vercel", configured=is_provider_configured(provider))


def _linear_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "linear")
    return _status_store_backed_status("linear", configured=is_provider_configured(provider))


def _amazon_live_status() -> dict:
    provider = next(p for p in list_providers() if p.value == "amazon")
    return _status_store_backed_status("amazon", configured=is_provider_configured(provider))


def _gmail_live_status() -> dict:
    return _oauth_live_status("gmail")


def _google_calendar_live_status() -> dict:
    return _oauth_live_status("google_calendar")


def _google_drive_live_status() -> dict:
    return _oauth_live_status("google_drive")


def _oauth_live_status(provider_id: str) -> dict:
    """Shared status shape for every OAuth2 connector: CONNECTED once the
    OAuth callback has stored a real access token (`oauth_connection_store`),
    regardless of whether "Test connection" has been clicked since —
    obtaining the token already proves the account is linked."""
    provider = next(p for p in list_providers() if p.value == provider_id)
    connection = oauth_connection_store.get(provider_id)
    return _status_store_backed_status(
        provider_id, configured=is_provider_configured(provider), force_connected=connection.connected
    )


def _github_live_status() -> dict:
    return _oauth_live_status("github")


def _slack_live_status() -> dict:
    return _oauth_live_status("slack")


def _notion_live_status() -> dict:
    return _oauth_live_status("notion")


def _gitlab_live_status() -> dict:
    return _oauth_live_status("gitlab")


_LIVE_STATUS_RESOLVERS = {
    "n8n": _n8n_live_status,
    "gemini": _gemini_live_status,
    "postgresql": _postgresql_live_status,
    "redis": _redis_live_status,
    "openai": _openai_live_status,
    "anthropic": _anthropic_live_status,
    "cloudflare": _cloudflare_live_status,
    "render": _render_live_status,
    "github": _github_live_status,
    "slack": _slack_live_status,
    "notion": _notion_live_status,
    "gitlab": _gitlab_live_status,
    "make": _make_live_status,
    "discord": _discord_live_status,
    "telegram": _telegram_live_status,
    "whatsapp": _whatsapp_live_status,
    "instagram": _instagram_live_status,
    "teams": _teams_live_status,
    "shopify": _shopify_live_status,
    "stripe": _stripe_live_status,
    "snapchat": _snapchat_live_status,
    "woocommerce": _woocommerce_live_status,
    "vercel": _vercel_live_status,
    "linear": _linear_live_status,
    "amazon": _amazon_live_status,
    "gmail": _gmail_live_status,
    "google_calendar": _google_calendar_live_status,
    "google_drive": _google_drive_live_status,
}


def _resolve_entry(spec: CatalogSpec) -> ConnectorEntry:
    live = _LIVE_STATUS_RESOLVERS.get(spec.id, dict)() if spec.implemented else {}
    return ConnectorEntry(
        id=spec.id,
        name=spec.name,
        description=spec.description,
        category=spec.category,
        connector_type=spec.connector_type,
        icon=spec.icon,
        auth_type=spec.auth_type,
        capabilities=spec.capabilities,
        capability_details=[
            CapabilityDetail(
                id=cap.id,
                label=cap.label,
                risk=str(cap.risk),
                requires_approval=requires_approval(cap),
            )
            for cap in resolve_all(spec.canonical_capabilities)
        ],
        kind=spec.kind,
        provider=spec.id,
        popular=spec.popular,
        documentation_url=spec.documentation_url,
        implemented=spec.implemented,
        requires=spec.requires,
        status=live.get("status", ConnectorStatusValue.AVAILABLE),
        configured=live.get("configured", False),
        connected=live.get("connected"),
        last_check=live.get("last_check"),
        last_check_latency_ms=live.get("last_check_latency_ms"),
        last_check_error=live.get("last_check_error"),
        last_execution=live.get("last_execution"),
        last_execution_success=live.get("last_execution_success"),
    )


@public_router.get("", response_model=list[ConnectorEntry])
async def list_catalog_route() -> list[ConnectorEntry]:
    """The full connector catalog with live status. Public — no secrets are
    ever included here, only whether something is configured/connected, so
    the Integration Hub can render for any visitor regardless of whether an
    operator API key is set in this browser."""
    return [_resolve_entry(spec) for spec in list_catalog()]


@public_router.get("/mcp/servers", response_model=list[MCPServerPublic])
async def list_mcp_servers_route() -> list[MCPServerPublic]:
    """Redacted MCP server list — never includes secret_value."""
    return [record.to_public() for record in mcp_store.list()]


@router.post("/mcp/servers", response_model=MCPServerPublic, status_code=201)
async def create_mcp_server_route(payload: MCPServerCreate) -> MCPServerPublic:
    # The endpoint is a URL this server will request on the operator's behalf,
    # with their configured bearer token attached — refuse the ones that turn
    # that into an SSRF primitive before storing it.
    try:
        validate_outbound_url(payload.endpoint)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    record = mcp_store.create(payload)
    return record.to_public()


@router.post("/mcp/servers/{server_id}/test", response_model=MCPServerPublic)
async def test_mcp_server_route(server_id: str) -> MCPServerPublic:
    record = mcp_store.get(server_id)
    if record is None:
        raise HTTPException(status_code=404, detail="MCP server not found")

    # Re-checked here and not only at creation: DNS can change underneath a
    # stored endpoint. This narrows the rebinding window rather than closing
    # it — see url_guard's docstring.
    try:
        validate_outbound_url(record.endpoint)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    client = MCPHttpClient(
        endpoint=record.endpoint,
        auth_type=record.auth_type,
        header_name=record.header_name,
        secret_value=record.secret_value,
        timeout_seconds=record.timeout_seconds,
    )
    connected, latency_ms, error, capabilities = await client.discover()
    mcp_store.record_check(server_id, connected=connected, latency_ms=latency_ms, error=error, capabilities=capabilities)
    return mcp_store.get(server_id).to_public()


@router.delete("/mcp/servers/{server_id}", status_code=204)
async def delete_mcp_server_route(server_id: str) -> None:
    if not mcp_store.delete(server_id):
        raise HTTPException(status_code=404, detail="MCP server not found")


@router.post("/{provider}/test", response_model=IntegrationStatus)
async def test_integration(provider: str) -> IntegrationStatus:
    normalized = provider.lower().strip()
    try:
        candidates = [p for p in list_providers() if p.value == normalized]
        provider_enum = candidates[0]
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Unknown integration provider: {provider}") from None

    if not is_provider_configured(provider_enum):
        requires = ", ".join(provider_requirements(provider_enum))
        raise HTTPException(
            status_code=503,
            detail=f"{provider_display_name(provider_enum)} is not configured. Set {requires}.",
        )

    try:
        adapter = build_integration_adapter(provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    connected, latency_ms, error = await adapter.test_connection()
    status_store.record_check(normalized, connected=connected, latency_ms=latency_ms, error=error)
    record = status_store.get(normalized)
    return IntegrationStatus(
        provider=provider_enum,
        name=provider_display_name(provider_enum),
        configured=True,
        requires=provider_requirements(provider_enum),
        connected=record.connected,
        last_check=record.last_check,
        last_check_latency_ms=record.last_check_latency_ms,
        last_check_error=record.last_check_error,
        last_execution=record.last_execution,
        last_execution_success=record.last_execution_success,
    )


@router.post("/execute", response_model=IntegrationResult)
async def execute_integration(payload: IntegrationExecutePayload) -> IntegrationResult:
    request = payload.request.model_copy(
        update={"correlation_id": get_or_create_correlation_id(payload.request.correlation_id)}
    )
    try:
        adapter = build_integration_adapter(payload.provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = await adapter.execute(request)
    status_store.record_execution(payload.provider.lower().strip(), success=result.success)
    return result


# ---------------------------------------------------------------------------
# OAuth2 authorization-code flow. `authorize` is operator-gated (only an
# authenticated operator can kick off connecting an account); `callback` is
# necessarily public — it's hit by the browser's redirect from the provider,
# which can't attach an X-API-Key header — and is protected instead by the
# single-use, short-lived state token minted in `authorize`.
# ---------------------------------------------------------------------------


@router.get("/oauth/{provider}/authorize", response_model=OAuthAuthorizeResponse)
async def oauth_authorize_route(provider: str) -> OAuthAuthorizeResponse:
    config = get_oauth_provider(provider)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Unknown OAuth provider: {provider}")
    try:
        url = build_authorize_url(config, oauth_state_store)
    except OAuthNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return OAuthAuthorizeResponse(authorize_url=url)


@public_router.get("/oauth/{provider}/callback", include_in_schema=False)
async def oauth_callback_route(
    provider: str, code: str | None = None, state: str | None = None, error: str | None = None
) -> RedirectResponse:
    frontend_target = f"{settings.frontend_base_url.rstrip('/')}/integrations"
    config = get_oauth_provider(provider)
    if config is None:
        return RedirectResponse(f"{frontend_target}?oauth=error&provider={quote(provider)}&message=unknown_provider")

    if error:
        oauth_connection_store.record_failure(config.id, error=error)
        return RedirectResponse(f"{frontend_target}?oauth=error&provider={config.id}&message={quote(error)}")

    if not state or oauth_state_store.consume(state) != config.id:
        return RedirectResponse(f"{frontend_target}?oauth=error&provider={config.id}&message=invalid_or_expired_state")

    if not code:
        return RedirectResponse(f"{frontend_target}?oauth=error&provider={config.id}&message=missing_code")

    try:
        await exchange_code(config, code=code, connection_store=oauth_connection_store)
    except (OAuthNotConfigured, OAuthExchangeError) as exc:
        return RedirectResponse(f"{frontend_target}?oauth=error&provider={config.id}&message={quote(str(exc))}")

    return RedirectResponse(f"{frontend_target}?oauth=connected&provider={config.id}")


@router.delete("/oauth/{provider}", status_code=204)
async def oauth_disconnect_route(provider: str) -> None:
    config = get_oauth_provider(provider)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Unknown OAuth provider: {provider}")
    oauth_connection_store.disconnect(config.id)

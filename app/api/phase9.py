from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import require_api_key
from app.core.config import settings
from app.core.correlation import get_or_create_correlation_id
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
    ConnectorEntry,
    ConnectorStatusValue,
    IntegrationRequest,
    IntegrationResult,
    IntegrationStatus,
)
from app.integrations.status_store import IntegrationStatusStore

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


_LIVE_STATUS_RESOLVERS = {
    "n8n": _n8n_live_status,
    "gemini": _gemini_live_status,
    "postgresql": _postgresql_live_status,
    "redis": _redis_live_status,
    "openai": _openai_live_status,
    "anthropic": _anthropic_live_status,
    "cloudflare": _cloudflare_live_status,
    "render": _render_live_status,
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
    record = mcp_store.create(payload)
    return record.to_public()


@router.post("/mcp/servers/{server_id}/test", response_model=MCPServerPublic)
async def test_mcp_server_route(server_id: str) -> MCPServerPublic:
    record = mcp_store.get(server_id)
    if record is None:
        raise HTTPException(status_code=404, detail="MCP server not found")

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

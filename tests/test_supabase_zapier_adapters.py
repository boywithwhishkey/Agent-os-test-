from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.models import IntegrationRequest
from app.integrations.supabase import SupabaseAdapter
from app.integrations.zapier import ZapierWebhookAdapter


@pytest.mark.anyio
async def test_supabase_reads_only_configured_table() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://demo.supabase.co/rest/v1/events?select=%2A&limit=5"
        assert request.headers["apikey"] == "anon-key"
        assert request.headers["authorization"] == "Bearer anon-key"
        return httpx.Response(200, json=[{"id": 1}])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await SupabaseAdapter(
            url="https://demo.supabase.co",
            anon_key="anon-key",
            read_table="events",
            client=client,
        ).run_capability("data.record.read", {"limit": 5})
    finally:
        await client.aclose()
    assert result == [{"id": 1}]


@pytest.mark.anyio
async def test_zapier_webhook_preserves_workflow_and_correlation_id() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://hooks.zapier.com/hooks/catch/123/abc"
        assert request.headers["x-agent-os-correlation-id"] == "corr-1"
        assert json.loads(request.content) == {"_workflow": "notify", "value": 7}
        return httpx.Response(200, json={"status": "success"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await ZapierWebhookAdapter(
            webhook_url="https://hooks.zapier.com/hooks/catch/123/abc", client=client
        ).execute(
            IntegrationRequest(
                workflow="notify", payload={"value": 7}, correlation_id="corr-1"
            )
        )
    finally:
        await client.aclose()
    assert result.success is True
    assert result.status_code == 200


@pytest.mark.anyio
async def test_zapier_connection_probe_does_not_trigger_post() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        return httpx.Response(405)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await ZapierWebhookAdapter(
            webhook_url="https://hooks.zapier.com/hooks/catch/123/abc", client=client
        ).test_connection()
    finally:
        await client.aclose()
    assert result[0] is True


def test_last_connectors_validate_fixed_targets() -> None:
    with pytest.raises(RuntimeError, match="HTTPS"):
        ZapierWebhookAdapter(webhook_url="http://hooks.zapier.com/hook")
    with pytest.raises(RuntimeError, match="SUPABASE_READ_TABLE"):
        SupabaseAdapter(
            url="https://demo.supabase.co", anon_key="anon-key", read_table="events;drop"
        )

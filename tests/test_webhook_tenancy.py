from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.tenant import current_tenant_id
from app.webhooks.consumer import WebhookConsumer
from app.webhooks.tenancy import (
    WebhookTenantNotConfigured,
    payload_identifiers,
    resolve_webhook_tenant,
)


def test_webhook_tenant_map_supports_account_specific_routes_and_fallbacks():
    settings = Settings(
        AGENT_OS_WEBHOOK_TENANT_MAP='{"shopify":"operator","shopify:store.myshopify.com":"merchant-a"}'
    )
    assert settings.webhook_tenant_routes == {
        "shopify": "operator",
        "shopify:store.myshopify.com": "merchant-a",
    }
    assert resolve_webhook_tenant(
        "shopify",
        identifiers=["store.myshopify.com"],
        routes=settings.webhook_tenant_routes,
        default_tenant="operator",
    ) == "merchant-a"
    assert resolve_webhook_tenant(
        "shopify",
        identifiers=["other.myshopify.com"],
        routes=settings.webhook_tenant_routes,
        default_tenant="operator",
    ) == "operator"


def test_webhook_tenant_map_fails_closed_for_unknown_or_ambiguous_routes():
    with pytest.raises(WebhookTenantNotConfigured, match="No webhook tenant route"):
        resolve_webhook_tenant(
            "stripe",
            identifiers=["acct_unknown"],
            routes={"stripe:acct_known": "tenant-a"},
            default_tenant="operator",
        )
    with pytest.raises(WebhookTenantNotConfigured, match="ambiguous"):
        resolve_webhook_tenant(
            "meta",
            identifiers=["page-1", "phone-1"],
            routes={"meta:page-1": "tenant-a", "meta:phone-1": "tenant-b"},
            default_tenant="operator",
        )


def test_payload_identifiers_extract_only_provider_account_ids():
    assert payload_identifiers(
        "meta",
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "waba-1",
                    "changes": [{"value": {"metadata": {"phone_number_id": "phone-1"}}}],
                }
            ],
        },
    ) == ["whatsapp_business_account", "waba-1", "phone-1"]
    assert payload_identifiers(
        "shopify", {}, {"shop_domain": "store.myshopify.com"}
    ) == ["store.myshopify.com"]
    assert payload_identifiers(
        "whatsapp",
        {
            "object": "whatsapp_business_account",
            "entry": [{"id": "waba-2", "changes": [{"value": {"phone_number_id": "phone-2"}}]}],
        },
    ) == ["whatsapp_business_account", "waba-2", "phone-2"]


@pytest.mark.asyncio
async def test_webhook_consumer_scopes_workflow_execution_to_job_tenant():
    class Definitions:
        async def get(self, workflow_id):
            return {"id": workflow_id}

    class Engine:
        async def start(self, definition, context, *, correlation_id):
            assert current_tenant_id.get() == "merchant-a"
            return {"workflow_id": definition["id"], "correlation_id": correlation_id}

    consumer = WebhookConsumer(
        definitions=Definitions(), engine=Engine(), routes={"stripe": "workflow-1"}
    )
    from app.queue.base import QueueJob

    result = await consumer.handle(
        QueueJob(
            type="connector.webhook",
            payload={
                "provider": "stripe",
                "body": '{"id":"evt_1","type":"payment_intent.succeeded"}',
                "delivery_id": "stripe:evt_1",
                "tenant_id": "merchant-a",
            },
        )
    )
    assert result["workflow_id"] == "workflow-1"
    assert current_tenant_id.get() is None

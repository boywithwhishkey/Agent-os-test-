from __future__ import annotations

import pytest

from app.queue.base import QueueJob
from app.webhooks.consumer import WebhookConsumer, WebhookWorkflowNotConfigured


class Definitions:
    def __init__(self, definition=None):
        self.definition = definition

    async def get(self, workflow_id):
        return self.definition if workflow_id == "workflow-1" else None


class Engine:
    def __init__(self):
        self.calls = []

    async def start(self, definition, context, *, correlation_id):
        self.calls.append((definition, context, correlation_id))
        return {"workflow_id": definition["id"], "correlation_id": correlation_id}


@pytest.mark.asyncio
async def test_consumer_routes_only_by_operator_allowlist():
    engine = Engine()
    consumer = WebhookConsumer(
        definitions=Definitions({"id": "workflow-1"}),
        engine=engine,
        routes={"telegram": "workflow-1"},
    )
    result = await consumer.handle(
        QueueJob(
            type="connector.webhook",
            correlation_id="corr-1",
            payload={
                "provider": "telegram",
                "body": "{\"update_id\":1}",
                "delivery_id": "telegram:abc",
            },
        )
    )
    assert result == {"workflow_id": "workflow-1", "correlation_id": "corr-1"}
    assert engine.calls[0][1]["webhook"]["delivery_id"] == "telegram:abc"
    assert engine.calls[0][1]["webhook"]["event_type"] == "update.received"


@pytest.mark.asyncio
async def test_consumer_refuses_unconfigured_provider():
    consumer = WebhookConsumer(
        definitions=Definitions({"id": "workflow-1"}), engine=Engine(), routes={}
    )
    with pytest.raises(WebhookWorkflowNotConfigured, match="telegram"):
        await consumer.handle(
            QueueJob(
                type="connector.webhook",
                payload={"provider": "telegram", "body": "{}", "delivery_id": "telegram:abc"},
            )
        )

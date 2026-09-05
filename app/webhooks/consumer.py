from __future__ import annotations

from typing import Any

from app.queue.base import QueueJob


class WebhookWorkflowNotConfigured(RuntimeError):
    """Raised when a verified provider has no explicit workflow route."""


class WebhookConsumer:
    """Turn verified webhook jobs into configured workflow runs.

    Provider payloads never choose a workflow themselves. The deployment
    operator supplies a provider-to-workflow allowlist; unknown providers and
    missing definitions fail into the worker's retry/dead-letter path.
    """

    def __init__(self, *, definitions: Any, engine: Any, routes: dict[str, str]) -> None:
        self.definitions = definitions
        self.engine = engine
        self.routes = {key.strip().lower(): value.strip() for key, value in routes.items()}

    async def handle(self, job: QueueJob) -> Any:
        if job.type != "connector.webhook":
            raise ValueError(f"Unsupported webhook job type: {job.type}")
        provider = job.payload.get("provider")
        body = job.payload.get("body")
        delivery = job.payload.get("delivery_id")
        if not all(
            isinstance(value, str) and value.strip() for value in (provider, body, delivery)
        ):
            raise ValueError("Webhook job is missing provider, body, or delivery_id")
        workflow_id = self.routes.get(provider.lower())
        if workflow_id is None:
            raise WebhookWorkflowNotConfigured(
                f"No workflow route is configured for webhook provider {provider}"
            )
        definition = await self.definitions.get(workflow_id)
        if definition is None:
            raise WebhookWorkflowNotConfigured(
                f"Webhook workflow definition {workflow_id} does not exist"
            )
        context = {
            "webhook": {
                "provider": provider,
                "body": body,
                "delivery_id": delivery,
            }
        }
        return await self.engine.start(
            definition,
            context,
            correlation_id=job.correlation_id or delivery,
        )

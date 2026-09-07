from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.tenant import current_tenant_id
from app.queue.base import QueueJob
from app.webhooks.events import normalize_webhook


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
        tenant_id = job.payload.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            # Jobs created before tenant routing was introduced remain
            # processable in the single-operator deployment mode. New API
            # ingress always stamps an explicit tenant id into the job.
            tenant_id = settings.oauth_tenant_id
        token = current_tenant_id.set(tenant_id.strip())
        try:
            return await self._handle_in_tenant(job, tenant_id.strip())
        finally:
            current_tenant_id.reset(token)

    async def _handle_in_tenant(self, job: QueueJob, tenant_id: str) -> Any:
        provider = job.payload.get("provider")
        body = job.payload.get("body")
        delivery = job.payload.get("delivery_id")
        metadata = job.payload.get("metadata")
        if not all(
            isinstance(value, str) and value.strip() for value in (provider, body, delivery)
        ):
            raise ValueError("Webhook job is missing provider, body, or delivery_id")
        normalized_provider = provider.lower()
        tenant_route = f"{tenant_id.strip().lower()}:{normalized_provider}"
        # A tenant-specific route is more precise than the legacy provider
        # route. The latter remains useful for a single shared workflow in
        # operator mode, while multi-tenant deployments can pin each tenant's
        # event stream to its own definition.
        workflow_id = self.routes.get(tenant_route) or self.routes.get(normalized_provider)
        if workflow_id is None:
            raise WebhookWorkflowNotConfigured(
                f"No workflow route is configured for webhook provider {provider}"
            )
        definition = await self.definitions.get(workflow_id)
        if definition is None:
            raise WebhookWorkflowNotConfigured(
                f"Webhook workflow definition {workflow_id} does not exist"
            )
        event = normalize_webhook(
            provider,
            body,
            delivery,
            metadata if isinstance(metadata, dict) else None,
        )
        context = {
            "webhook": {
                "provider": provider,
                "body": body,
                "delivery_id": delivery,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "payload": event.payload,
            }
        }
        return await self.engine.start(
            definition,
            context,
            correlation_id=job.correlation_id or delivery,
        )

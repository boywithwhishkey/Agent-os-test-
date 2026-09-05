from __future__ import annotations

from app.core.config import settings
from app.queue.factory import build_job_queue
from app.queue.worker import JobWorker
from app.webhooks.consumer import WebhookConsumer


def build_webhook_worker(*, definitions, engine) -> JobWorker:
    """Build the worker used by a deployment's webhook-consumer process."""
    consumer = WebhookConsumer(
        definitions=definitions,
        engine=engine,
        routes=settings.webhook_workflow_routes,
    )
    return JobWorker(
        build_job_queue(),
        consumer.handle,
        queue_name="webhooks",
        max_retries=settings.max_retries,
        backoff_base_seconds=settings.retry_backoff_base,
    )

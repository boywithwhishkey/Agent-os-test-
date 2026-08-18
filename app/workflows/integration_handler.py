from __future__ import annotations

from typing import Any

from app.integrations.base import IntegrationAdapter
from app.integrations.models import IntegrationRequest


async def run_integration_step(
    *,
    adapter: IntegrationAdapter,
    workflow: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
    timeout_seconds: float = 30.0,
) -> Any:
    result = await adapter.execute(
        IntegrationRequest(
            workflow=workflow,
            payload=payload,
            correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
        )
    )
    if not result.success:
        raise RuntimeError(result.error or "Integration execution failed")
    return result.data

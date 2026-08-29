from __future__ import annotations

import time

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.queue.redis_queue import RedisJobQueue


class RedisAdapter(IntegrationAdapter):
    """Verifies REDIS_URL is reachable with a PING, independent of whether
    Redis is the currently active queue backend."""

    def __init__(self, *, redis_url: str | None = None, queue: RedisJobQueue | None = None) -> None:
        self.redis_url = redis_url or settings.redis_url
        self._queue = queue
        if not self._queue and not self.redis_url:
            raise RuntimeError("REDIS_URL is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.REDIS,
            request,
            reason="Redis is a queue backend, not a triggered workflow.",
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_queue = self._queue is None
        queue = self._queue or RedisJobQueue(self.redis_url)

        started = time.perf_counter()
        try:
            client = await queue._get_client()
            await client.ping()
            return True, (time.perf_counter() - started) * 1000, None
        except Exception as exc:  # noqa: BLE001 - any backend failure means "not reachable"
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_queue:
                await queue.close()

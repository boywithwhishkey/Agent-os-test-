from __future__ import annotations

from app.core.config import settings
from app.queue.base import JobQueue, QueueJob


class RedisJobQueue(JobQueue):
    def __init__(self, url: str, prefix: str = "agent-os") -> None:
        self.url = url
        self.prefix = prefix
        self._client = None

    @classmethod
    def from_settings(cls) -> RedisJobQueue:
        url = settings.redis_url.strip()
        if not url:
            raise RuntimeError("REDIS_URL is required for Redis queue")
        # Namespaced per environment so a shared Redis cannot cross-feed jobs
        # between production and staging.
        return cls(url, settings.queue_namespace)

    async def _get_client(self):
        if self._client is None:
            try:
                from redis.asyncio import Redis
            except ImportError as exc:
                raise RuntimeError(
                    'redis is required for Redis queue. Run: pip install -e ".[persistence]"'
                ) from exc
            self._client = Redis.from_url(self.url, decode_responses=True)
        return self._client

    def _key(self, queue: str) -> str:
        return f"{self.prefix}:queue:{queue}"

    async def enqueue(self, job: QueueJob) -> str:
        client = await self._get_client()
        await client.rpush(self._key(job.queue), job.model_dump_json())
        return job.id

    async def dequeue(self, queue: str = "default", timeout: int = 1) -> QueueJob | None:
        client = await self._get_client()
        result = await client.blpop(self._key(queue), timeout=timeout)
        if not result:
            return None
        _, payload = result
        return QueueJob.model_validate_json(payload)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

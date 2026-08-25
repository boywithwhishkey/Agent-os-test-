from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.queue.base import JobQueue, QueueJob

JobHandler = Callable[[QueueJob], Awaitable[None]]


class JobWorker:
    """Pulls jobs from a queue, acknowledging via successful handling.

    Failed jobs are retried with backoff up to max_retries, then moved to a
    dead-letter queue so a single poison message can't block the queue.
    """

    def __init__(
        self,
        queue: JobQueue,
        handler: JobHandler,
        *,
        queue_name: str = "default",
        max_retries: int = 2,
        backoff_base_seconds: float = 0.25,
    ) -> None:
        self.queue = queue
        self.handler = handler
        self.queue_name = queue_name
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.dead_letter_queue = f"{queue_name}:dead-letter"

    async def process_one(self, *, timeout: int = 1) -> bool:
        job = await self.queue.dequeue(self.queue_name, timeout=timeout)
        if job is None:
            return False
        await self._handle(job)
        return True

    async def _handle(self, job: QueueJob) -> None:
        try:
            await self.handler(job)
        except Exception:  # noqa: BLE001 - handler failures become retries or dead-letters
            job.attempts += 1
            if job.attempts <= self.max_retries:
                await asyncio.sleep(self.backoff_base_seconds * (2 ** (job.attempts - 1)))
                job.queue = self.queue_name
                await self.queue.enqueue(job)
            else:
                job.queue = self.dead_letter_queue
                await self.queue.enqueue(job)

    async def run_forever(self, *, poll_timeout: int = 1) -> None:
        while True:
            processed = await self.process_one(timeout=poll_timeout)
            if not processed:
                await asyncio.sleep(poll_timeout)

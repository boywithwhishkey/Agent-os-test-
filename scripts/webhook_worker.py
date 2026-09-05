#!/usr/bin/env python3
"""Run the isolated THYNACT webhook consumer process.

The worker reads only the ``webhooks`` queue and routes provider events through
the operator-configured ``AGENT_OS_WEBHOOK_WORKFLOW_MAP`` allowlist. It never
accepts a workflow id from the incoming provider payload.
"""

from __future__ import annotations

import asyncio

from app.api.phase8 import definitions, engine
from app.queue.webhook_worker import build_webhook_worker


async def main() -> None:
    worker = build_webhook_worker(definitions=definitions, engine=engine)
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

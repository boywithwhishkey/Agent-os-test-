from __future__ import annotations

from typing import Any

_resources: list[Any] = []


def register_resource(resource: Any) -> Any:
    """Track a resource with an async close() for shutdown cleanup."""
    _resources.append(resource)
    return resource


async def close_all() -> None:
    while _resources:
        resource = _resources.pop()
        await resource.close()

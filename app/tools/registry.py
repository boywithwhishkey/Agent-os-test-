from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.tools.models import ToolRisk

ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]


@dataclass(slots=True)
class RegisteredTool:
    name: str
    description: str
    risk: ToolRisk
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, tool: RegisteredTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> RegisteredTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list_tools(self) -> list[RegisteredTool]:
        return list(self._tools.values())

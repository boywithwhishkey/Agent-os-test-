from __future__ import annotations

from app.tools.models import ToolCall, ToolExecutionResult, ToolRisk
from app.tools.registry import ToolRegistry


class ToolExecutor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def execute(self, call: ToolCall) -> ToolExecutionResult:
        try:
            tool = self.registry.get(call.tool)
        except KeyError as exc:
            return ToolExecutionResult(
                tool=call.tool,
                success=False,
                risk=ToolRisk.HIGH_RISK,
                error=str(exc),
            )

        if tool.risk in {ToolRisk.WRITE, ToolRisk.HIGH_RISK} and not call.approved:
            return ToolExecutionResult(
                tool=tool.name,
                success=False,
                risk=tool.risk,
                error="Human approval required",
                approval_required=True,
            )

        try:
            output = await tool.handler(call.arguments)
            return ToolExecutionResult(
                tool=tool.name,
                success=True,
                risk=tool.risk,
                output=output,
            )
        except Exception as exc:
            return ToolExecutionResult(
                tool=tool.name,
                success=False,
                risk=tool.risk,
                error=f"{type(exc).__name__}: {exc}",
            )

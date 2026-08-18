from __future__ import annotations

from app.tools.audit import InMemoryToolAuditLog
from app.tools.models import ToolCall, ToolExecutionResult, ToolRisk
from app.tools.policy import ToolPolicy
from app.tools.registry import ToolRegistry


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        policy: ToolPolicy,
        audit: InMemoryToolAuditLog,
    ):
        self.registry = registry
        self.policy = policy
        self.audit = audit

    async def execute(
        self,
        call: ToolCall,
        *,
        approval_id: str | None = None,
    ) -> ToolExecutionResult:
        try:
            tool = self.registry.get(call.tool)
        except KeyError as exc:
            result = ToolExecutionResult(
                tool=call.tool,
                success=False,
                risk=ToolRisk.HIGH_RISK,
                error=str(exc),
            )
            self._audit(result)
            return result

        decision = self.policy.authorize(
            tool_name=tool.name,
            risk=tool.risk,
            approval_id=approval_id,
        )
        if not decision.allowed:
            result = ToolExecutionResult(
                tool=tool.name,
                success=False,
                risk=tool.risk,
                error=decision.error,
                approval_required=decision.approval_required,
            )
            self._audit(result)
            return result

        try:
            output = await tool.handler(call.arguments)
            result = ToolExecutionResult(
                tool=tool.name,
                success=True,
                risk=tool.risk,
                output=output,
            )
        except Exception as exc:
            result = ToolExecutionResult(
                tool=tool.name,
                success=False,
                risk=tool.risk,
                error=f"{type(exc).__name__}: {exc}",
            )

        self._audit(result)
        return result

    def _audit(self, result: ToolExecutionResult) -> None:
        self.audit.record(
            tool=result.tool,
            success=result.success,
            risk=result.risk.value,
            approval_required=result.approval_required,
            error=result.error,
        )

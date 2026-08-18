from __future__ import annotations

from dataclasses import dataclass

from app.tools.approvals import ApprovalStore
from app.tools.models import ToolRisk


@dataclass(slots=True)
class ToolPolicyDecision:
    allowed: bool
    approval_required: bool = False
    error: str | None = None


class ToolPolicy:
    def __init__(self, approvals: ApprovalStore):
        self.approvals = approvals

    def authorize(
        self,
        *,
        tool_name: str,
        risk: ToolRisk,
        approval_id: str | None = None,
    ) -> ToolPolicyDecision:
        if risk == ToolRisk.READ:
            return ToolPolicyDecision(allowed=True)

        if not approval_id:
            return ToolPolicyDecision(
                allowed=False,
                approval_required=True,
                error="Trusted approval required",
            )

        grant = self.approvals.consume(approval_id, tool_name)
        if grant is None:
            return ToolPolicyDecision(
                allowed=False,
                approval_required=True,
                error="Invalid or expired approval",
            )

        return ToolPolicyDecision(allowed=True)

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from app.tools.models import ApprovalGrant


class ApprovalStore(ABC):
    @abstractmethod
    async def issue(
        self, tool: str, approved_by: str, reason: str | None = None
    ) -> ApprovalGrant:
        raise NotImplementedError

    @abstractmethod
    async def consume(self, approval_id: str, tool: str) -> ApprovalGrant | None:
        raise NotImplementedError


class InMemoryApprovalStore(ApprovalStore):
    def __init__(self) -> None:
        self._grants: dict[str, ApprovalGrant] = {}

    async def issue(
        self, tool: str, approved_by: str, reason: str | None = None
    ) -> ApprovalGrant:
        grant = ApprovalGrant(
            approval_id=str(uuid4()),
            tool=tool,
            approved_by=approved_by,
            reason=reason,
        )
        self._grants[grant.approval_id] = grant
        return grant

    async def consume(self, approval_id: str, tool: str) -> ApprovalGrant | None:
        grant = self._grants.get(approval_id)
        if grant is None or grant.tool != tool:
            return None
        self._grants.pop(approval_id, None)
        return grant

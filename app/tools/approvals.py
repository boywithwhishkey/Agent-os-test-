from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from app.core.tenant import get_current_tenant
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
    def __init__(self, *, tenant_id: str = "operator") -> None:
        self._tenant_id = tenant_id
        self._grants: dict[tuple[str, str], ApprovalGrant] = {}

    def _key(self, approval_id: str) -> tuple[str, str]:
        return get_current_tenant(self._tenant_id), approval_id

    async def issue(
        self, tool: str, approved_by: str, reason: str | None = None
    ) -> ApprovalGrant:
        grant = ApprovalGrant(
            approval_id=str(uuid4()),
            tool=tool,
            approved_by=approved_by,
            reason=reason,
        )
        self._grants[self._key(grant.approval_id)] = grant
        return grant

    async def consume(self, approval_id: str, tool: str) -> ApprovalGrant | None:
        key = self._key(approval_id)
        grant = self._grants.get(key)
        if grant is None or grant.tool != tool:
            return None
        self._grants.pop(key, None)
        return grant

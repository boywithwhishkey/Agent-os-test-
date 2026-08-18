from __future__ import annotations

from abc import ABC, abstractmethod

from app.integrations.models import IntegrationRequest, IntegrationResult


class IntegrationAdapter(ABC):
    @abstractmethod
    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        raise NotImplementedError

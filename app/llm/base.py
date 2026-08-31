from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class LLMRequest:
    system: str
    prompt: str

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> str:
        raise NotImplementedError

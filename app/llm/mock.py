from .base import LLMProvider, LLMRequest

class MockLLMProvider(LLMProvider):
    async def generate(self, request: LLMRequest) -> str:
        return f"MOCK_RESULT: {request.prompt}"

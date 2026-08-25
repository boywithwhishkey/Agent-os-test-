from .base import LLMProvider, LLMRequest


class MockLLMProvider(LLMProvider):
    async def generate(self, request: LLMRequest) -> str:
        if "planning agent" in request.system:
            return (
                '{"jobs":['
                '{"name":"researcher","task":"Identify the key requirements and constraints.",'
                '"system_prompt":"You are a research specialist."},'
                '{"name":"builder","task":"Propose a practical implementation approach.",'
                '"system_prompt":"You are an engineering specialist."},'
                '{"name":"reviewer","task":"Define how the objective should be verified.",'
                '"system_prompt":"You are a quality specialist."}'
                ']}'
            )
        if "verification agent" in request.system:
            return "Approved: deterministic mock specialist outputs are available."
        if "final synthesis agent" in request.system:
            return "MOCK_FINAL: deterministic synthesis complete."
        return f"MOCK_RESULT: {request.prompt}"

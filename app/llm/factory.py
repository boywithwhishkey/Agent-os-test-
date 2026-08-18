import os
from .base import LLMProvider
from .mock import MockLLMProvider

def build_llm_provider() -> LLMProvider:
    provider = os.getenv("AGENT_OS_LLM_PROVIDER", "mock").lower().strip()
    if provider == "mock":
        return MockLLMProvider()
    raise RuntimeError(
        f"Unsupported LLM provider: {provider}. "
        "Keep provider=mock until a live provider adapter is configured."
    )

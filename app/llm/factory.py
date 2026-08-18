import os

from .base import LLMProvider
from .mock import MockLLMProvider


def build_llm_provider() -> LLMProvider:
    provider = os.getenv("AGENT_OS_LLM_PROVIDER", "mock").lower().strip()

    if provider == "mock":
        return MockLLMProvider()

    if provider == "gemini":
        from .gemini import GeminiLLMProvider
        return GeminiLLMProvider()

    raise RuntimeError(
        f"Unsupported LLM provider: {provider}. "
        "Supported providers: mock, gemini."
    )

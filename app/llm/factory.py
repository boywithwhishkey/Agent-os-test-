from app.core.config import get_settings

from .base import LLMProvider
from .mock import MockLLMProvider


def build_llm_provider() -> LLMProvider:
    provider = get_settings().llm_provider.lower().strip()

    if provider == "mock":
        return MockLLMProvider()

    if provider == "gemini":
        from .gemini import GeminiLLMProvider
        return GeminiLLMProvider()

    raise RuntimeError(
        f"Unsupported LLM provider: {provider}. "
        "Supported providers: mock, gemini."
    )

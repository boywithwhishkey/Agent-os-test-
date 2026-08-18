import pytest

from app.llm.factory import build_llm_provider
from app.llm.gemini import GeminiLLMProvider


def test_mock_remains_default(monkeypatch):
    monkeypatch.delenv("AGENT_OS_LLM_PROVIDER", raising=False)
    provider = build_llm_provider()
    assert provider.__class__.__name__ == "MockLLMProvider"


def test_gemini_requires_key(monkeypatch):
    monkeypatch.setenv("AGENT_OS_LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        build_llm_provider()


def test_gemini_configuration(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_OS_LLM_MODEL", "test-model")
    provider = GeminiLLMProvider()
    assert provider.api_key == "test-key"
    assert provider.model == "test-model"

import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def configured_test_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "test-api-key")
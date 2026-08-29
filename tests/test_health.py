from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "THYNACT"
    assert body["llm_provider"] == "mock"
    assert body["backends"]["memory"] == "memory"
    assert body["backends"]["queue"] == "memory"


def test_cors_preflight_allows_api_key_and_correlation_headers() -> None:
    response = client.options(
        "/api/v1/tasks",
        headers={
            "Origin": "https://app.thynact.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key, X-Correlation-ID, Content-Type",
        },
    )

    assert response.status_code == 200
    allowed = response.headers["access-control-allow-headers"].lower()
    assert "x-api-key" in allowed
    assert "x-correlation-id" in allowed


def test_cors_exposes_correlation_id_header() -> None:
    response = client.get("/health", headers={"Origin": "https://app.thynact.com"})

    assert response.status_code == 200
    exposed = response.headers.get("access-control-expose-headers", "").lower()
    assert "x-correlation-id" in exposed

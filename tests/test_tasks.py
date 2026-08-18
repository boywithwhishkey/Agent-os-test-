from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_get_task() -> None:
    create_response = client.post(
        "/api/v1/tasks",
        json={
            "objective": "Build the first Master Agent workflow",
            "priority": "high",
            "project_id": "agent-os",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "pending"
    assert created["priority"] == "high"

    get_response = client.get(f"/api/v1/tasks/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


def test_missing_task_returns_404() -> None:
    response = client.get("/api/v1/tasks/does-not-exist")

    assert response.status_code == 404

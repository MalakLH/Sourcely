from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json()["status"] == "healthy"


def test_chat():

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Explain Kubernetes Pods"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tool_used"] == "docs"
    assert "[STUB]" in data["answer"]


def test_empty_message():

    response = client.post(
        "/api/v1/chat",
        json={
            "message": ""
        },
    )

    assert response.status_code == 422
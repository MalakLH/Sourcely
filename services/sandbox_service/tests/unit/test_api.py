import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.schemas.response import ExecutionResponse

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/sandbox/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "sandbox-service",
    }


def test_execute_success(monkeypatch):
    def fake_execute(request):
        assert request.language == "python"
        assert request.code == "print(1 + 1)"
        assert request.timeout == 5

        return ExecutionResponse(
            status="success",
            stdout="2\n",
            stderr="",
            exit_code=0,
            duration_ms=100,
            container_id="test123",
        )

    monkeypatch.setattr(
        routes.executor,
        "execute",
        fake_execute,
    )

    response = client.post(
        "/api/v1/sandbox/execute",
        json={
            "language": "python",
            "code": "print(1 + 1)",
            "timeout": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["stdout"] == "2\n"
    assert response.json()["exit_code"] == 0


@pytest.mark.parametrize(
    "payload",
    [
        {
            "language": "javascript",
            "code": "console.log('hello')",
            "timeout": 5,
        },
        {
            "language": "python",
            "code": "print('hello')",
            "timeout": 11,
        },
        {
            "language": "python",
            "code": "",
            "timeout": 5,
        },
    ],
)
def test_execute_rejects_invalid_requests(payload):
    response = client.post(
        "/api/v1/sandbox/execute",
        json=payload,
    )

    assert response.status_code == 422

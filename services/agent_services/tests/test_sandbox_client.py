
import httpx
import pytest

from app.clients.sandbox_client import (
    SandboxClient,
    SandboxClientError,
)


def test_execute_success(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs

        return httpx.Response(
            200,
            request=httpx.Request(
                "POST",
                url,
            ),
            json={
                "status": "success",
                "stdout": "2\n",
                "stderr": "",
                "exit_code": 0,
                "duration_ms": 100.0,
                "container_id": "test-container",
            },
        )
    monkeypatch.setattr(
        "app.clients.sandbox_client.httpx.post",
        fake_post,
    )

    client = SandboxClient(
        base_url="http://sandbox-service:8001",
        api_key="test-secret",
    )

    result = client.execute("print(1 + 1)")

    assert result["status"] == "success"
    assert result["stdout"] == "2\n"

    assert captured["url"] == (
        "http://sandbox-service:8001/api/v1/sandbox/execute"
    )

    assert captured["kwargs"]["json"]["code"] == "print(1 + 1)"
    assert captured["kwargs"]["json"]["language"] == "python"
    assert captured["kwargs"]["headers"]["X-Sandbox-Token"] == "test-secret"


def test_execute_rejects_empty_code():
    client = SandboxClient(api_key="test-secret")

    with pytest.raises(SandboxClientError, match="cannot be empty"):
        client.execute("   ")


def test_execute_rejects_missing_api_key(monkeypatch):
    monkeypatch.delenv("SANDBOX_API_KEY", raising=False)

    client = SandboxClient(api_key="")

    with pytest.raises(SandboxClientError, match="not configured"):
        client.execute("print('hello')")


def test_execute_handles_http_error(monkeypatch):
    def fake_post(url, **kwargs):
        return httpx.Response(
            401,
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(
        "app.clients.sandbox_client.httpx.post",
        fake_post,
    )

    client = SandboxClient(api_key="test-secret")

    with pytest.raises(SandboxClientError, match="HTTP 401"):
        client.execute("print('hello')")


def test_execute_handles_connection_error(monkeypatch):
    def fake_post(url, **kwargs):
        raise httpx.ConnectError(
            "Connection refused",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(
        "app.clients.sandbox_client.httpx.post",
        fake_post,
    )

    client = SandboxClient(api_key="test-secret")

    with pytest.raises(SandboxClientError, match="Could not connect"):
        client.execute("print('hello')")

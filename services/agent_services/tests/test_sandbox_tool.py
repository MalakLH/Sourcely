
from unittest.mock import Mock

from app.tools.base import ToolName, ToolRequest, ToolStatus
from app.tools.sandbox_tool import run_sandbox_tool


def create_fake_client(response=None, side_effect=None):
    client = Mock()

    if side_effect:
        client.execute.side_effect = side_effect
    else:
        client.execute.return_value = response

    return client


def test_sandbox_tool_success():
    client = create_fake_client(
        response={
            "status": "success",
            "stdout": "2\n",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 100.0,
            "container_id": "test-container",
        }
    )

    request = ToolRequest(
        query="Run this code",
        metadata={
            "code": "print(1 + 1)",
            "timeout": 5,
        },
    )

    result = run_sandbox_tool(request, client)

    assert result.status == ToolStatus.SUCCESS
    assert result.tool == ToolName.SANDBOX
    assert "2" in result.content
    assert result.metadata["exit_code"] == 0

    client.execute.assert_called_once_with(
        code="print(1 + 1)",
        timeout=5,
    )


def test_sandbox_tool_rejects_missing_code():
    client = create_fake_client()

    request = ToolRequest(
        query="Run this code",
        metadata={},
    )

    result = run_sandbox_tool(request, client)

    assert result.status == ToolStatus.ERROR
    assert result.metadata.get("execution_status") is None
    client.execute.assert_not_called()


def test_sandbox_tool_rejects_invalid_timeout():
    client = create_fake_client()

    request = ToolRequest(
        query="Run this code",
        metadata={
            "code": "print(1)",
            "timeout": 50,
        },
    )

    result = run_sandbox_tool(request, client)

    assert result.status == ToolStatus.ERROR
    assert "timeout" in result.content.lower()
    client.execute.assert_not_called()


def test_sandbox_tool_handles_execution_failure():
    client = create_fake_client(
        response={
            "status": "failed",
            "stdout": "",
            "stderr": "NameError: name 'x' is not defined",
            "exit_code": 1,
            "duration_ms": 100.0,
            "container_id": "test-container",
        }
    )

    request = ToolRequest(
        query="Run this code",
        metadata={
            "code": "print(x)",
        },
    )

    result = run_sandbox_tool(request, client)

    assert result.status == ToolStatus.ERROR
    assert result.metadata["execution_status"] == "failed"
    assert "NameError" in result.content


def test_sandbox_tool_handles_timeout():
    client = create_fake_client(
        response={
            "status": "timeout",
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "duration_ms": 5000.0,
            "container_id": "test-container",
        }
    )

    request = ToolRequest(
        query="Run this code",
        metadata={
            "code": "while True: pass",
        },
    )

    result = run_sandbox_tool(request, client)

    assert result.status == ToolStatus.ERROR
    assert result.metadata["execution_status"] == "timeout"


def test_sandbox_tool_handles_communication_failure():
    from app.clients.sandbox_client import SandboxClientError

    client = create_fake_client(
        side_effect=SandboxClientError("Could not connect")
    )

    request = ToolRequest(
        query="Run this code",
        metadata={
            "code": "print(1)",
        },
    )

    result = run_sandbox_tool(request, client)

    assert result.status == ToolStatus.ERROR
    assert result.metadata["execution_status"] == "error"
    assert "Could not connect" in result.content

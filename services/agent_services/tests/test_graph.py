import pytest

from app.agent.graph import agent_graph
from app.tools.base import ToolName, ToolRequest, ToolResult, ToolStatus


def test_docs_workflow():

    result = agent_graph.invoke(
        {
            "query": "Explain Kubernetes Pods",
            "selected_tool": "",
            "tool_result": None,
            "answer": "",
        }
    )

    assert result["selected_tool"] == "docs"
    assert "[STUB]" in result["answer"]


@pytest.mark.asyncio
async def test_web_workflow(monkeypatch):
    async def mock_run_web_tool(request: ToolRequest) -> ToolResult:
        return ToolResult(
            status=ToolStatus.SUCCESS,
            tool=ToolName.WEB,
            content="Mock Web Guide result",
            sources=[],
        )

    monkeypatch.setattr(
        "app.agent.graph.run_web_tool",
        mock_run_web_tool,
    )

    result = await agent_graph.ainvoke(
        {
            "query": "Find GitHub repositories about RAG",
            "selected_tool": "",
            "tool_result": None,
            "answer": "",
        }
    )

    assert result["selected_tool"] == "web"
    assert result["answer"] == "Mock Web Guide result"


def test_sandbox_workflow(monkeypatch):
    def mock_run_sandbox_tool(request: ToolRequest) -> ToolResult:
        assert request.query == "Run this code"
        assert request.metadata["code"] == "print(1 + 1)"
        assert request.metadata["timeout"] == 5

        return ToolResult(
            status=ToolStatus.SUCCESS,
            tool=ToolName.SANDBOX,
            content="Execution status: success\n\nStandard output:\n2\n",
            metadata={
                "execution_status": "success",
                "exit_code": 0,
            },
        )

    monkeypatch.setattr(
        "app.agent.graph.run_sandbox_tool",
        mock_run_sandbox_tool,
    )

    result = agent_graph.invoke(
        {
            "query": "Run this code",
            "code": "print(1 + 1)",
            "timeout": 5,
            "selected_tool": "",
            "tool_result": None,
            "answer": "",
        }
    )

    assert result["selected_tool"] == "sandbox"
    assert result["answer"] == ("Execution status: success\n\nStandard output:\n2\n")
    assert result["tool_result"]["metadata"]["exit_code"] == 0


def test_sandbox_workflow_without_code():
    result = agent_graph.invoke(
        {
            "query": "Run this code",
            "selected_tool": "",
            "tool_result": None,
            "answer": "",
        }
    )

    assert result["selected_tool"] == "sandbox"
    assert result["tool_result"]["status"] == "error"
    assert "No valid Python code" in result["answer"]

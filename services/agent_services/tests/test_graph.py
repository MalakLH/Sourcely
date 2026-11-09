
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


def test_sandbox_workflow():

    result = agent_graph.invoke(
        {
            "query": "Scan this code for vulnerabilities",
            "selected_tool": "",
            "tool_result": None,
            "answer": "",
        }
    )

    assert result["selected_tool"] == "sandbox"

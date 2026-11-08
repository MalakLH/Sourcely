from app.agent.graph import agent_graph


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


def test_web_workflow():

    result = agent_graph.invoke(
        {
            "query": "Find GitHub repositories about RAG",
            "selected_tool": "",
            "tool_result": None,
            "answer": "",
        }
    )

    assert result["selected_tool"] == "web"


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

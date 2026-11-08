from app.agent.router import route_request
from app.tools.base import ToolName


def test_docs_routing():

    result = route_request("Explain Kubernetes Pods")

    assert result == ToolName.DOCS


def test_web_routing():

    result = route_request("Find GitHub repositories about RAG")

    assert result == ToolName.WEB


def test_sandbox_routing():

    result = route_request("Scan this code for vulnerabilities")

    assert result == ToolName.SANDBOX

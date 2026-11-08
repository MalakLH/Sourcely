import json
import sys

from langchain_ollama import ChatOllama
from langchain_core.tools import tool


# testing the tool calling capabilities with ollama and seeing if it can tell which tool is needed 

@tool
def docs_expert(query: str) -> str:
    """Search official technical documentation."""
    return f"Docs Expert selected for: {query}"


@tool
def web_guide(query: str) -> str:
    """Find tutorials, articles and GitHub repositories."""
    return f"Web Guide selected for: {query}"


@tool
def secure_sandbox(code: str) -> str:
    """Request an isolated code security analysis."""
    return "Sandbox analysis requested."


TOOLS = [
    docs_expert,
    web_guide,
    secure_sandbox,
]


def main():

    model_name = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b"

    model = ChatOllama(
        model=model_name,
        temperature=0,
    )

    model_with_tools = model.bind_tools(TOOLS)

    test_queries = [
        "Explain how Kubernetes Deployments work.",
        "Find GitHub repositories about LangGraph.",
        "Check this Python code for security problems.",
    ]

    for query in test_queries:

        print(f"\nQuery: {query}")

        response = model_with_tools.invoke(query)

        print("Tool calls:")

        for call in response.tool_calls:
            print(json.dumps(call, indent=2))


if __name__ == "__main__":
    main()
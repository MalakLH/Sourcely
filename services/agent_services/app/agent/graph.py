from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agent.router import route_request
from app.agent.state import AgentState
from app.tools.base import ToolRequest
from app.tools.docs_tool import run_docs_tool
from app.tools.sandbox_tool import run_sandbox_tool
from app.tools.web_tool import run_web_tool


def router_node(state: AgentState) -> dict:

    selected_tool = route_request(state["query"])

    return {"selected_tool": selected_tool.value}


def docs_node(state: AgentState) -> dict:

    result = run_docs_tool(ToolRequest(query=state["query"]))

    return {"tool_result": result.model_dump()}


async def web_node(state: AgentState) -> dict:

    result = await run_web_tool(ToolRequest(query=state["query"]))

    return {"tool_result": result.model_dump()}


def sandbox_node(state: AgentState) -> dict:

    result = run_sandbox_tool(ToolRequest(query=state["query"]))

    return {"tool_result": result.model_dump()}


def final_node(state: AgentState) -> dict:

    result = state["tool_result"]

    answer = result["content"] if result else "No result available."

    return {"answer": answer}


def select_tool(
    state: AgentState,
) -> Literal["docs", "web", "sandbox"]:

    return state["selected_tool"]


def build_graph():

    builder = StateGraph(AgentState)

    builder.add_node("router", router_node)
    builder.add_node("docs", docs_node)
    builder.add_node("web", web_node)
    builder.add_node("sandbox", sandbox_node)
    builder.add_node("final", final_node)

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        select_tool,
        {
            "docs": "docs",
            "web": "web",
            "sandbox": "sandbox",
        },
    )

    builder.add_edge("docs", "final")
    builder.add_edge("web", "final")
    builder.add_edge("sandbox", "final")

    builder.add_edge("final", END)

    return builder.compile()


agent_graph = build_graph()

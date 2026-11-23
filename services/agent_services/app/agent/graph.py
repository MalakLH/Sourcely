import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agent.router import route_request
from app.agent.state import AgentState
from app.tools.base import ToolRequest, ToolStatus
from app.tools.docs_tool import run_docs_tool
from app.tools.sandbox_tool import run_sandbox_tool
from app.tools.web_tool import run_web_tool

logger = logging.getLogger(__name__)

# Confidence threshold for docs fallback
DOCS_CONFIDENCE_THRESHOLD = 0.65


def router_node(state: AgentState) -> dict:
    selected_tool = route_request(
        state["query"],
        has_code=bool(state.get("code")),
    )

    return {"selected_tool": selected_tool.value}


def docs_node(state: AgentState) -> dict:
    result = run_docs_tool(ToolRequest(query=state["query"]))

    # Check confidence and trigger web fallback if needed
    tool_result = result.model_dump()
    
    # Extract confidence from metadata or result
    confidence_str = tool_result.get("metadata", {}).get("confidence")
    
    # Parse confidence score (could be "low", "medium", "high" or a float)
    should_fallback = False
    
    if confidence_str:
        if isinstance(confidence_str, str):
            # Map string confidence to numeric
            confidence_map = {"low": 0.3, "medium": 0.6, "high": 0.85}
            confidence_score = confidence_map.get(confidence_str.lower(), 0.5)
        else:
            confidence_score = float(confidence_str)
        
        if confidence_score < DOCS_CONFIDENCE_THRESHOLD:
            logger.info(
                f"Docs confidence {confidence_score:.2f} below threshold {DOCS_CONFIDENCE_THRESHOLD} "
                f"- triggering web fallback"
            )
            should_fallback = True
    
    # Store docs result for potential combination AND set tool_result for non-fallback case
    return {
        "docs_result": tool_result,
        "tool_result": tool_result if not should_fallback else None,  # Set tool_result if not falling back
        "needs_web_fallback": should_fallback,
        "tools_used": ["docs"],
    }


async def web_node(state: AgentState) -> dict:
    result = await run_web_tool(ToolRequest(query=state["query"]))
    web_result = result.model_dump()
    
    # Check if this is a fallback call
    docs_result = state.get("docs_result")
    
    if docs_result:
        # Combine docs + web results
        logger.info("Combining docs and web results for low-confidence fallback")
        
        # Merge content
        docs_content = docs_result.get("content", "")
        web_content = web_result.get("content", "")
        
        combined_content = f"{docs_content}\n\n--- Additional Web Resources ---\n\n{web_content}"
        
        # Merge sources
        docs_sources = docs_result.get("sources", [])
        web_sources = web_result.get("sources", [])
        combined_sources = docs_sources + web_sources
        
        # Create combined result
        combined_result = {
            "status": "success",
            "tool": "docs+web",  # Indicate both tools used
            "content": combined_content,
            "sources": combined_sources,
            "metadata": {
                **docs_result.get("metadata", {}),
                "fallback_triggered": True,
                "web_sources_count": len(web_sources),
            },
        }
        
        return {
            "tool_result": combined_result,
            "needs_web_fallback": False,
            "tools_used": ["docs", "web"],
        }
    else:
        # Direct web query (not a fallback)
        return {
            "tool_result": web_result,
            "needs_web_fallback": False,
            "tools_used": ["web"],
        }


def sandbox_node(state: AgentState) -> dict:
    result = run_sandbox_tool(
        ToolRequest(
            query=state["query"],
            metadata={
                "code": state.get("code"),
                "timeout": state.get("timeout", 5),
            },
        )
    )

    return {
        "tool_result": result.model_dump(),
        "needs_web_fallback": False,
        "tools_used": ["sandbox"],
    }


def final_node(state: AgentState) -> dict:
    result = state.get("tool_result")
    
    if not result:
        # Fallback scenario - use docs result if available
        result = state.get("docs_result", {})
    
    answer = result.get("content", "No result available.") if result else "No result available."

    return {"answer": answer}


def select_tool(state: AgentState) -> Literal["docs", "web", "sandbox"]:
    return state["selected_tool"]


def check_web_fallback(state: AgentState) -> Literal["web", "final"]:
    """
    Conditional edge that checks if web fallback is needed after docs retrieval.
    
    If docs confidence is below threshold, route to web_node for additional results.
    Otherwise, proceed to final_node.
    """
    needs_fallback = state.get("needs_web_fallback", False)
    
    if needs_fallback:
        logger.info("Routing to web fallback after low-confidence docs result")
        return "web"
    else:
        return "final"


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

    # Add conditional fallback from docs to web
    builder.add_conditional_edges(
        "docs",
        check_web_fallback,
        {
            "web": "web",
            "final": "final",
        },
    )

    builder.add_edge("web", "final")
    builder.add_edge("sandbox", "final")

    builder.add_edge("final", END)

    return builder.compile()


agent_graph = build_graph()

import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import agent_graph
from app.tools.base import ToolStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["agent"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    session_id: Optional[str] = Field(None, description="Session identifier for context tracking")
    code: Optional[str] = Field(None, description="Optional code snippet to execute or scan")
    timeout: Optional[int] = Field(5, ge=1, le=10, description="Sandbox execution timeout in seconds")


class QueryResponse(BaseModel):
    answer: str = Field(..., description="Agent's answer to the query")
    tool_used: str = Field(..., description="Tool that was invoked (docs, web, sandbox)")
    citations: list[str] = Field(default_factory=list, description="Source URLs or references")
    sources: list[dict] = Field(default_factory=list, description="Detailed source information")
    confidence: Optional[str] = Field(None, description="Confidence level from docs retrieval")
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    status: str = Field(..., description="Execution status (success or error)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata from tool execution")


@router.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest) -> QueryResponse:
    """
    Main agent query endpoint that routes requests through LangGraph workflow.

    This endpoint:
    1. Accepts a user query (and optional code snippet)
    2. Routes the query to the appropriate tool (docs, web, or sandbox) via LangGraph
    3. Executes the tool and returns structured results
    4. Includes citations, confidence scores, and execution time

    Args:
        request: QueryRequest with query, optional session_id, code, and timeout

    Returns:
        QueryResponse with answer, tool used, citations, and execution metadata
    """
    start_time = time.time()

    try:
        # Build initial state for LangGraph
        initial_state = {
            "query": request.query,
            "selected_tool": "",
            "tool_result": None,
            "answer": "",
        }

        # Add optional code and timeout if provided
        if request.code:
            initial_state["code"] = request.code

        if request.timeout is not None:
            initial_state["timeout"] = request.timeout

        # Execute LangGraph workflow
        logger.info(
            f"Processing query (session: {request.session_id or 'none'}): {request.query[:100]}..."
        )

        result = await agent_graph.ainvoke(initial_state)

        # Extract results
        tool_used = result.get("selected_tool", "unknown")
        tools_used = result.get("tools_used", [tool_used])  # Support multiple tools
        tool_result = result.get("tool_result")
        answer = result.get("answer", "No answer generated.")
        
        # Handle case where tool_result might be None
        if not tool_result:
            tool_result = {}

        # Extract metadata from tool result
        tool_status = tool_result.get("status", "unknown")
        sources = tool_result.get("sources", [])
        metadata = tool_result.get("metadata", {})
        error = tool_result.get("error")

        # Build citations list (URLs from sources)
        citations = []
        if isinstance(sources, list):
            for source in sources:
                if isinstance(source, str):
                    citations.append(source)
                elif isinstance(source, dict) and "url" in source:
                    citations.append(source["url"])

        # Extract confidence if available (from docs tool)
        confidence = metadata.get("confidence")
        
        # Determine tool display (handle combined tools)
        if len(tools_used) > 1:
            tool_display = "+".join(tools_used)  # "docs+web"
        else:
            tool_display = tools_used[0] if tools_used else tool_used

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Log successful execution
        logger.info(
            f"Query completed: tools={tool_display}, status={tool_status}, "
            f"time={execution_time_ms:.2f}ms"
        )

        # Build response
        response = QueryResponse(
            answer=answer,
            tool_used=tool_display,  # Can be "docs", "web", "sandbox", or "docs+web"
            citations=citations,
            sources=sources if isinstance(sources, list) else [],
            confidence=confidence,
            execution_time_ms=round(execution_time_ms, 2),
            status=tool_status,
            metadata=metadata,
        )

        # If tool execution failed, log error
        if tool_status == ToolStatus.ERROR:
            logger.warning(f"Tool execution error: {error}")

        return response

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(f"Agent query error: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Agent execution failed",
                "message": str(e),
                "execution_time_ms": round(execution_time_ms, 2),
            },
        )


@router.get("/health")
async def health_check() -> dict:
    """Simple health check endpoint for agent API."""
    return {
        "status": "healthy",
        "service": "agent-api",
        "graph_compiled": agent_graph is not None,
    }

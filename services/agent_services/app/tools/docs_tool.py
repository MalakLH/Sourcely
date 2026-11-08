from app.tools.base import ToolName, ToolRequest, ToolResult, ToolStatus


def run_docs_tool(request: ToolRequest) -> ToolResult:
    return ToolResult(
        status=ToolStatus.SUCCESS,
        tool=ToolName.DOCS,
        content=f"[STUB] Docs Expert received: {request.query}",
        sources=[],
    )

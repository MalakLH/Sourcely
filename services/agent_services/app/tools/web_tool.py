from app.tools.base import ToolName, ToolRequest, ToolResult, ToolStatus


def run_web_tool(request: ToolRequest) -> ToolResult:
    return ToolResult(
        status=ToolStatus.SUCCESS,
        tool=ToolName.WEB,
        content=f"[STUB] Web Guide received: {request.query}",
        sources=[],
    )
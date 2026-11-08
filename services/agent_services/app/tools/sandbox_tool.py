from app.tools.base import ToolName, ToolRequest, ToolResult, ToolStatus


def run_sandbox_tool(request: ToolRequest) -> ToolResult:
    return ToolResult(
        status=ToolStatus.SUCCESS,
        tool=ToolName.SANDBOX,
        content="Sandbox execution is not implemented yet.",
        metadata={"execution_status": "not_implemented"},
    )

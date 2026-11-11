from app.clients.sandbox_client import SandboxClient, SandboxClientError
from app.tools.base import ToolName, ToolRequest, ToolResult, ToolStatus


def run_sandbox_tool(
    request: ToolRequest,
    client: SandboxClient | None = None,
) -> ToolResult:
    # 1. Extract executable code from structured metadata.
    code = request.metadata.get("code")

    if not isinstance(code, str) or not code.strip():
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.SANDBOX,
            content="No valid Python code was provided for execution.",
            error="Missing or invalid code.",
        )

    # 2. Validate the requested execution timeout.
    timeout = request.metadata.get("timeout", 5)

    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 10:
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.SANDBOX,
            content="Invalid execution timeout. It must be between 1 and 10 seconds.",
            error="Invalid timeout.",
        )

    # 3. Use the injected client, or create the default client.
    sandbox_client = client or SandboxClient()

    # 4. Send the code to the sandbox service.
    try:
        result = sandbox_client.execute(
            code=code,
            timeout=timeout,
        )

    except SandboxClientError as exc:
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.SANDBOX,
            content=f"Sandbox communication failed: {exc}",
            error=str(exc),
            metadata={"execution_status": "error"},
        )

    # 5. Interpret the sandbox response.
    execution_status = result.get("status")

    if execution_status not in {"success", "failed", "timeout"}:
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.SANDBOX,
            content="Sandbox returned an invalid execution status.",
            error="Invalid sandbox response.",
            metadata={"execution_status": "error"},
        )

    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")

    # 6. Format the execution output for the agent.
    output_parts = [
        f"Execution status: {execution_status}",
    ]

    if stdout:
        output_parts.append(f"Standard output:\n{stdout}")

    if stderr:
        output_parts.append(f"Standard error:\n{stderr}")

    if not stdout and not stderr:
        output_parts.append("No output was produced.")

    content = "\n\n".join(output_parts)

    # 7. Convert the execution result into ToolResult.
    return ToolResult(
        status=(ToolStatus.SUCCESS if execution_status == "success" else ToolStatus.ERROR),
        tool=ToolName.SANDBOX,
        content=content,
        error=stderr or (execution_status if execution_status != "success" else None),
        metadata={
            "execution_status": execution_status,
            "exit_code": result.get("exit_code"),
            "duration_ms": result.get("duration_ms"),
            "container_id": result.get("container_id"),
            "stdout": stdout,
            "stderr": stderr,
        },
    )

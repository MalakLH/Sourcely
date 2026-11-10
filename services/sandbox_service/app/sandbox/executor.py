
from app.core.config import settings
from app.sandbox.container import DockerContainerManager
from app.schemas.request import ExecutionRequest
from app.schemas.response import ExecutionResponse


class SandboxExecutor:

    def __init__(self):
        self.container_manager = DockerContainerManager()

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        if len(request.code) > settings.max_code_size:
            raise ValueError("Code exceeds maximum allowed size.")

        if request.timeout > settings.max_execution_timeout:
            raise ValueError("Requested timeout exceeds server limit.")

        result = self.container_manager.execute(
            code=request.code,
            timeout=request.timeout,
        )

        return ExecutionResponse(
            status=result.status,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
            container_id=result.container_id,
        )

    def close(self) -> None:
        self.container_manager.close()

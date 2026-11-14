import os

from app.core.config import settings
from app.ledger.models import ExecutionRecord
from app.ledger.storage import ExecutionLedger
from app.sandbox.container import DockerContainerManager
from app.schemas.request import ExecutionRequest
from app.schemas.response import ExecutionResponse


class SandboxExecutor:
    MAX_LEDGER_RETRIES = 10

    def __init__(
        self,
        ledger: ExecutionLedger | None = None,
    ):
        self.container_manager = DockerContainerManager()

        database_path = os.getenv(
            "SANDBOX_LEDGER_PATH",
            "/data/execution_ledger.db",
        )

        self.ledger = ledger or ExecutionLedger(database_path)

    def _record_execution(
        self,
        *,
        code: str,
        stdout: str,
        stderr: str,
        status: str,
        exit_code: int | None,
        duration_ms: float,
    ) -> None:
        """
        Append an execution record.

        If another execution appends first, rebuild the record against
        the updated ledger head and retry.
        """
        for attempt in range(self.MAX_LEDGER_RETRIES):
            previous_hash = self.ledger.get_latest_hash()

            record = ExecutionRecord.create(
                status=status,
                exit_code=exit_code,
                duration_ms=duration_ms,
                code=code,
                stdout=stdout,
                stderr=stderr,
                previous_hash=previous_hash,
            )

            try:
                self.ledger.append(record)
                return
            except ValueError as exc:
                if "current ledger head" not in str(exc):
                    raise

                if attempt == self.MAX_LEDGER_RETRIES - 1:
                    raise RuntimeError(
                        "Unable to append execution after concurrent ledger updates."
                    ) from exc

        raise RuntimeError("Execution ledger append failed.")

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        if len(request.code) > settings.max_code_size:
            raise ValueError("Code exceeds maximum allowed size.")

        if request.timeout > settings.max_execution_timeout:
            raise ValueError("Requested timeout exceeds server limit.")

        result = self.container_manager.execute(
            code=request.code,
            timeout=request.timeout,
        )

        # Record the execution before returning the response.
        self._record_execution(
            code=request.code,
            stdout=result.stdout,
            stderr=result.stderr,
            status=result.status,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
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

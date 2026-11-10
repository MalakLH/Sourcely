
from typing import Literal

from pydantic import BaseModel


class ExecutionResponse(BaseModel):
    status: Literal["success", "failed", "timeout"]

    stdout: str = ""
    stderr: str = ""

    exit_code: int | None = None

    duration_ms: float

    container_id: str | None = None

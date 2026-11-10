
from typing import Literal

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    language: Literal["python"] = "python"

    code: str = Field(
        min_length=1,
        max_length=12_000,
    )

    timeout: int = Field(
        default=5,
        ge=1,
        le=10,
    )

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolName(str, Enum):
    DOCS = "docs"
    WEB = "web"
    SANDBOX = "sandbox"


class ToolStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class ToolRequest(BaseModel):
    query: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    status: ToolStatus
    tool: ToolName
    content: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# prevents inconsistent tool naming


class ToolName(StrEnum):
    DOCS = "docs"
    WEB = "web"
    SANDBOX = "sandbox"


# makes errors and successful executions distinguishable


class ToolStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


# defines what the agent sends to a tool


class ToolRequest(BaseModel):
    query: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# defines what a tool must return


class ToolResult(BaseModel):
    status: ToolStatus
    tool: ToolName
    content: str

    # allows Docs Expert and Web Guide to provide references,
    # a list of resources for example titles, urls...
    sources: list[dict[str, Any]] = Field(default_factory=list)

    # allows Sandbox to return additional information such as scan statistics
    metadata: dict[str, Any] = Field(default_factory=dict)

    error: str | None = None

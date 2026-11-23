from typing import NotRequired, TypedDict


class AgentState(TypedDict):
    query: str
    selected_tool: str
    tool_result: dict | None
    answer: str

    # Optional execution inputs
    code: NotRequired[str | None]
    timeout: NotRequired[int]
    
    # Fallback tracking
    needs_web_fallback: NotRequired[bool]
    docs_result: NotRequired[dict | None]
    web_result: NotRequired[dict | None]
    tools_used: NotRequired[list[str]]  # Track multiple tools when fallback happens

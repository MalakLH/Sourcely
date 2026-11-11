from typing import NotRequired, TypedDict


class AgentState(TypedDict):
    query: str
    selected_tool: str
    tool_result: dict | None
    answer: str

    # Optional execution inputs
    code: NotRequired[str | None]
    timeout: NotRequired[int]

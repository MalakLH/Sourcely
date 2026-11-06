from typing import TypedDict

from app.tools.base import ToolResult

# LangGraph works with a shared state that moves through nodes
# Every node can read the state and return updates to it

class AgentState(TypedDict):
    query: str
    selected_tool: str
    tool_result: dict | None
    answer: str
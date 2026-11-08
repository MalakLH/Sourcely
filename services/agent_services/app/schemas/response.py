from pydantic import BaseModel


class ChatResponse(BaseModel):
    answer: str
    tool_used: str
    tool_result: dict | None = None

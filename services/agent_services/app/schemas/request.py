from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    code: str | None = Field(default=None, max_length=12000)
    timeout: int = Field(default=5, ge=1, le=10)

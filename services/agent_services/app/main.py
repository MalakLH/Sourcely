from fastapi import FastAPI

from app.agent.graph import agent_graph
from app.core.config import settings
from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse


app = FastAPI(
    title=settings.app_name,
    description="Sourcely AI Developer Agent",
    version="0.1.0",
)


@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "agent-service",
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    initial_state = {
        "query": request.message,
        "selected_tool": "",
        "tool_result": None,
        "answer": "",
    }

    result = agent_graph.invoke(initial_state)

    return ChatResponse(
        answer=result["answer"],
        tool_used=result["selected_tool"],
        tool_result=result["tool_result"],
    )
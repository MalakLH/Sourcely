
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Isolated code execution service for Sourcely",
    version="0.1.0",
)

app.include_router(
    router,
    prefix="/api/v1/sandbox",
    tags=["Sandbox"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Sourcely Sandbox!",
        "status": "running",
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router)


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "status": "running",
        "version": "0.1.0",
        "supported_scanners": ["bandit", "semgrep"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

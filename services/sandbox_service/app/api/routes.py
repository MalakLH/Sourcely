
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.schemas.request import ExecutionRequest
from app.schemas.response import ExecutionResponse
from app.sandbox.executor import SandboxExecutor

router = APIRouter()

executor = SandboxExecutor()


@router.post("/execute", response_model=ExecutionResponse)
async def execute_code(request: ExecutionRequest):
    try:
        return await run_in_threadpool(
            executor.execute,
            request,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "sandbox-service",
    }

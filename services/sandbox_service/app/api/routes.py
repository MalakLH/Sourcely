
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.sandbox.executor import SandboxExecutor
from app.schemas.request import ExecutionRequest
from app.schemas.response import ExecutionResponse

router = APIRouter()
executor = SandboxExecutor()


def verify_sandbox_token(
    token: str | None = Header(default=None, alias="X-Sandbox-Token"),
) -> None:
    expected_token = settings.api_key.get_secret_value()

    # Fail closed if the service has no configured API key.
    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Sandbox authentication is not configured.",
        )

    if token is None or not secrets.compare_digest(token, expected_token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing sandbox token.",
        )


@router.post(
    "/execute",
    response_model=ExecutionResponse,
    dependencies=[Depends(verify_sandbox_token)],
)
async def execute_code(request: ExecutionRequest):
    try:
        return await run_in_threadpool(executor.execute, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/health")
async def health():
    return {"status": "ok", "service": "sandbox-service"}

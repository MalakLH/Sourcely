
import os
from typing import Any

import httpx


class SandboxClientError(Exception):
    """Raised when communication with the sandbox service fails."""


class SandboxClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.base_url = (
            base_url or os.getenv(
                "SANDBOX_BASE_URL",
                "http://localhost:8001",
            )
        ).rstrip("/")

        self.api_key = api_key or os.getenv("SANDBOX_API_KEY")

    def execute(
        self,
        code: str,
        timeout: int = 5,
    ) -> dict[str, Any]:

        if not self.api_key:
            raise SandboxClientError(
                "Sandbox API key is not configured."
            )

        if not code or not code.strip():
            raise SandboxClientError(
                "Python code cannot be empty."
            )

        payload = {
            "language": "python",
            "code": code,
            "timeout": timeout,
        }

        headers = {
            "Content-Type": "application/json",
            "X-Sandbox-Token": self.api_key,
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/v1/sandbox/execute",
                json=payload,
                headers=headers,
                timeout=httpx.Timeout(
                    timeout=timeout + 5,
                    connect=3.0,
                ),
            )

            response.raise_for_status()

            result = response.json()

            if not isinstance(result, dict):
                raise SandboxClientError(
                    "Sandbox returned an invalid response."
                )

            return result

        except httpx.TimeoutException as exc:
            raise SandboxClientError(
                "Sandbox request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise SandboxClientError(
                f"Sandbox returned HTTP {exc.response.status_code}."
            ) from exc

        except httpx.RequestError as exc:
            raise SandboxClientError(
                "Could not connect to the sandbox service."
            ) from exc

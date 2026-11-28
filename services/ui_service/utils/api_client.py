"""API client for communicating with backend services."""

import os

import httpx


class SourcelyAPIClient:
    """Client for Sourcely backend services."""

    def __init__(
        self,
        agent_url: str | None = None,
        scanner_url: str | None = None,
        docs_url: str | None = None,
        timeout: float = 30.0,
    ):
        self.agent_url = (
            agent_url
            or os.getenv(
                "AGENT_SERVICE_URL",
                "http://localhost:8000",
            )
        ).rstrip("/")

        self.scanner_url = (
            scanner_url
            or os.getenv(
                "SCANNER_SERVICE_URL",
                "http://localhost:8004",
            )
        ).rstrip("/")

        self.docs_url = (
            docs_url
            or os.getenv(
                "DOCS_SERVICE_URL",
                "http://localhost:8002",
            )
        ).rstrip("/")

        self.timeout = timeout

    async def query_agent(self, query: str, code: str | None = None) -> dict:
        """
        Send a query to the agent service.

        Args:
            query: User's question or request
            code: Optional code snippet to execute

        Returns:
            Response from agent with answer and metadata
        """
        payload = {"query": query}
        if code:
            payload["code"] = code

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.agent_url}/api/query",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def scan_code(
        self,
        code: str,
        language: str = "python",
        scanners: list[str] | None = None,
        include_explanations: bool = True,
    ) -> dict:
        """
        Scan code for vulnerabilities.

        Args:
            code: Code content to scan
            language: Programming language
            scanners: List of scanners to use
            include_explanations: Whether to generate LLM explanations

        Returns:
            Scan results with findings
        """
        if scanners is None:
            scanners = ["bandit", "semgrep"]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.scanner_url}/scan",
                json={
                    "code": code,
                    "language": language,
                    "scanners": scanners,
                    "include_explanations": include_explanations,
                },
            )
            response.raise_for_status()
            return response.json()

    async def explain_finding(
        self, finding: dict, code_context: str | None = None
    ) -> dict:
        """
        Get LLM explanation for a security finding.

        Args:
            finding: The finding to explain
            code_context: Optional code context

        Returns:
            Explanation with remediation advice
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.scanner_url}/explain",
                json={
                    "finding": finding,
                    "code_context": code_context,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_docs_stats(self) -> dict:
        """Get documentation service statistics."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.docs_url}/stats")
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> dict:
        """Check health of all services."""
        results = {}

        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check agent service
            try:
                response = await client.get(f"{self.agent_url}/health")
                results["agent"] = response.status_code == 200
            except httpx.HTTPError:
                results["agent"] = False

            # Check scanner service
            try:
                response = await client.get(f"{self.scanner_url}/health")
                results["scanner"] = response.status_code == 200
            except httpx.HTTPError:
                results["scanner"] = False

            # Check docs service
            try:
                response = await client.get(f"{self.docs_url}/health")
                results["docs"] = response.status_code == 200
            except httpx.HTTPError:
                results["docs"] = False

            # Webguide and Sandbox are internal, mark as unknown for now
            results["webguide"] = False
            results["sandbox"] = False

        return results

    async def execute_sandbox(
        self,
        code: str,
        language: str = "python",
        timeout: int = 5,
    ) -> dict:
        """
        Execute code in sandbox environment.

        Args:
            code: Code to execute
            language: Programming language
            timeout: Execution timeout in seconds

        Returns:
            Execution results with stdout, stderr, exit code
        """
        # Sandbox is internal, call via agent for now
        # In future, could expose sandbox endpoint or use agent's sandbox tool
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.agent_url}/api/query",
                json={
                    "query": f"Execute this {language} code",
                    "code": code,
                    "timeout": timeout,
                },
            )
            response.raise_for_status()
            return response.json()

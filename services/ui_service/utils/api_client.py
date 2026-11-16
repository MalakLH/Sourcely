"""API client for communicating with backend services."""

import httpx
from typing import Optional


class SourcelyAPIClient:
    """Client for Sourcely backend services."""

    def __init__(
        self,
        agent_url: str = "http://localhost:8000",
        scanner_url: str = "http://localhost:8002",
        docs_url: str = "http://localhost:8001",
        timeout: float = 30.0,
    ):
        self.agent_url = agent_url.rstrip("/")
        self.scanner_url = scanner_url.rstrip("/")
        self.docs_url = docs_url.rstrip("/")
        self.timeout = timeout

    async def query_agent(self, query: str) -> dict:
        """
        Send a query to the agent service.

        Args:
            query: User's question or request

        Returns:
            Response from agent with answer and metadata
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.agent_url}/api/query",
                json={"query": query},
            )
            response.raise_for_status()
            return response.json()

    async def scan_code(
        self,
        code: str,
        language: str = "python",
        scanners: list[str] = None,
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

    async def explain_finding(self, finding: dict, code_context: Optional[str] = None) -> dict:
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
            except Exception:
                results["agent"] = False

            # Check scanner service
            try:
                response = await client.get(f"{self.scanner_url}/health")
                results["scanner"] = response.status_code == 200
            except Exception:
                results["scanner"] = False

            # Check docs service
            try:
                response = await client.get(f"{self.docs_url}/health")
                results["docs"] = response.status_code == 200
            except Exception:
                results["docs"] = False

        return results

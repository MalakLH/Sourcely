#!/usr/bin/env python3
"""
Integration verification script for Sourcely services.

Tests all services and their integrations to ensure end-to-end functionality.
"""

import asyncio
import sys
from typing import Optional

import httpx


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


async def check_service_health(name: str, url: str) -> bool:
    """Check if a service is healthy."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            if response.status_code == 200:
                print(f"{Colors.GREEN}✓{Colors.END} {name} is healthy")
                return True
            else:
                print(f"{Colors.RED}✗{Colors.END} {name} returned {response.status_code}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} {name} is unreachable: {e}")
        return False


async def test_docs_ingestion(docs_url: str) -> bool:
    """Test documentation ingestion."""
    print(f"\n{Colors.BLUE}Testing documentation ingestion...{Colors.END}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Ingest all docs
            response = await client.post(f"{docs_url}/ingest/all")
            if response.status_code == 200:
                data = response.json()
                chunks = data.get("chunks_created", 0)
                docs = data.get("documents_processed", 0)
                print(f"{Colors.GREEN}✓{Colors.END} Ingested {docs} documents ({chunks} chunks)")
                return True
            else:
                print(f"{Colors.RED}✗{Colors.END} Ingestion failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Ingestion error: {e}")
        return False


async def test_docs_retrieval(docs_url: str) -> bool:
    """Test documentation retrieval."""
    print(f"\n{Colors.BLUE}Testing documentation retrieval...{Colors.END}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{docs_url}/retrieve",
                json={"query": "What is a Kubernetes Pod?", "top_k": 3},
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                confidence = data.get("confidence", "unknown")
                print(f"{Colors.GREEN}✓{Colors.END} Retrieved {len(results)} results (confidence: {confidence})")
                return True
            else:
                print(f"{Colors.RED}✗{Colors.END} Retrieval failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Retrieval error: {e}")
        return False


async def test_web_search(webguide_url: str) -> bool:
    """Test web search."""
    print(f"\n{Colors.BLUE}Testing web search...{Colors.END}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{webguide_url}/search",
                json={"query": "Docker best practices", "max_results": 5},
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                sources = data.get("sources_used", [])
                print(f"{Colors.GREEN}✓{Colors.END} Found {len(results)} results from {', '.join(sources)}")
                return True
            else:
                print(f"{Colors.RED}✗{Colors.END} Search failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Search error: {e}")
        return False


async def test_code_scanning(scanner_url: str) -> bool:
    """Test code scanning."""
    print(f"\n{Colors.BLUE}Testing code scanning...{Colors.END}")

    vulnerable_code = '''
password = "hardcoded123"
eval(user_input)
'''

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{scanner_url}/scan",
                json={
                    "code": vulnerable_code,
                    "language": "python",
                    "scanners": ["bandit"],
                    "include_explanations": False,
                },
            )
            if response.status_code == 200:
                data = response.json()
                total = data.get("total_findings", 0)
                by_severity = data.get("findings_by_severity", {})
                print(f"{Colors.GREEN}✓{Colors.END} Found {total} security issues:")
                for severity, count in by_severity.items():
                    if count > 0:
                        print(f"  - {severity}: {count}")
                return True
            else:
                print(f"{Colors.RED}✗{Colors.END} Scan failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Scan error: {e}")
        return False


async def test_agent_query(agent_url: str) -> bool:
    """Test agent query routing."""
    print(f"\n{Colors.BLUE}Testing agent query routing...{Colors.END}")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{agent_url}/api/query",
                json={"query": "What is a Kubernetes Service?"},
            )
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                tool_result = data.get("tool_result", {})
                tool = tool_result.get("tool", "unknown")
                print(f"{Colors.GREEN}✓{Colors.END} Agent routed to '{tool}' tool")
                print(f"  Answer preview: {answer[:100]}...")
                return True
            else:
                print(f"{Colors.RED}✗{Colors.END} Query failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Query error: {e}")
        return False


async def main():
    """Main verification function."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Sourcely Integration Verification{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    # Service URLs
    services = {
        "Agent Service": "http://localhost:8000",
        "Docs Service": "http://localhost:8001",
        "Scanner Service": "http://localhost:8002",
        "Web Guide Service": "http://localhost:8003",
        "UI Service": "http://localhost:8501",
    }

    # Health checks
    print(f"\n{Colors.BLUE}1. Checking service health...{Colors.END}")
    health_results = {}
    for name, url in services.items():
        if name == "UI Service":
            # Streamlit doesn't have /health endpoint, just check root
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        print(f"{Colors.GREEN}✓{Colors.END} {name} is running")
                        health_results[name] = True
                    else:
                        print(f"{Colors.RED}✗{Colors.END} {name} returned {response.status_code}")
                        health_results[name] = False
            except Exception as e:
                print(f"{Colors.RED}✗{Colors.END} {name} is unreachable")
                health_results[name] = False
        else:
            health_results[name] = await check_service_health(name, url)

    # If critical services are down, exit
    critical_services = ["Agent Service", "Docs Service", "Scanner Service", "Web Guide Service"]
    if not all(health_results.get(s, False) for s in critical_services):
        print(f"\n{Colors.RED}✗ Critical services are down. Please start all services first.{Colors.END}")
        print(f"\nRun: cd infrastructure/docker && docker-compose up -d")
        sys.exit(1)

    # Integration tests
    print(f"\n{Colors.BLUE}2. Running integration tests...{Colors.END}")

    test_results = {}

    # Test docs service
    test_results["Docs Ingestion"] = await test_docs_ingestion(services["Docs Service"])
    test_results["Docs Retrieval"] = await test_docs_retrieval(services["Docs Service"])

    # Test web guide service
    test_results["Web Search"] = await test_web_search(services["Web Guide Service"])

    # Test scanner service
    test_results["Code Scanning"] = await test_code_scanning(services["Scanner Service"])

    # Test agent service (end-to-end)
    test_results["Agent Query"] = await test_agent_query(services["Agent Service"])

    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Verification Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)

    for test_name, result in test_results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{status} - {test_name}")

    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}✓ All tests passed! ({passed_tests}/{total_tests}){Colors.END}")
        print(f"\n{Colors.GREEN}Sourcely is ready to use!{Colors.END}")
        print(f"\nAccess the UI at: {Colors.BLUE}http://localhost:8501{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠ Some tests failed ({passed_tests}/{total_tests} passed){Colors.END}")
        print(f"\nCheck service logs with: docker-compose logs <service-name>")

    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    sys.exit(0 if passed_tests == total_tests else 1)


if __name__ == "__main__":
    asyncio.run(main())

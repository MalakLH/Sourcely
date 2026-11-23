import asyncio
import logging
from typing import Optional

import httpx

from app.tools.base import ToolName, ToolRequest, ToolResult, ToolStatus

logger = logging.getLogger(__name__)

WEBGUIDE_SERVICE_URL = "http://sourcely-webguide:8003"


async def search_web_guide(
    query: str,
    max_results: int = 10,
) -> Optional[dict]:
    """
    Call the webguide-service /search endpoint asynchronously.

    Args:
        query: Search query
        max_results: Number of results to retrieve

    Returns:
        Response dict from webguide-service or None on error
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{WEBGUIDE_SERVICE_URL}/search",
                json={
                    "query": query,
                    "max_results": max_results,
                    "sources": ["searxng", "github"],
                    "include_github": True,
                },
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as e:
        logger.error(f"Error calling webguide-service: {e}")
        return None


def format_web_results(webguide_response: dict) -> tuple[str, list[str]]:
    """
    Format web guide results into a readable response with sources.

    Args:
        webguide_response: Response from webguide-service /search endpoint

    Returns:
        Tuple of (formatted_content, sources_list)
    """
    if not webguide_response or not webguide_response.get("results"):
        return "No web results found for your query.", []

    results = webguide_response["results"]
    sources_used = webguide_response.get("sources_used", [])

    # Build formatted response
    answer_parts = [
        f"Found {len(results)} relevant web resources (sources: {', '.join(sources_used)}):\n"
    ]

    sources = []

    for idx, result in enumerate(results, 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        snippet = result.get("snippet", "")
        source = result.get("source", "unknown")
        ranking_score = result.get("ranking_score", 0.0)

        # Format result
        result_text = f"\n**[{idx}] {title}**"

        # Add source indicator
        if source == "github":
            stars = result.get("stars")
            language = result.get("language")
            result_text += " 🔗 GitHub"
            if language:
                result_text += f" ({language})"
            if stars:
                result_text += f" ⭐ {stars:,}"
        else:
            result_text += f" 🌐 Web"

        result_text += f" [score: {ranking_score:.3f}]\n"

        # Add snippet if available
        if snippet:
            snippet_preview = snippet[:250] + "..." if len(snippet) > 250 else snippet
            result_text += f"{snippet_preview}\n"

        result_text += f"Link: {url}\n"

        answer_parts.append(result_text)
        sources.append(url)

    return "\n".join(answer_parts), sources


async def run_web_tool(request: ToolRequest) -> ToolResult:
    """
    Execute web search using the webguide-service.

    This tool:
    1. Calls the webguide-service /search endpoint
    2. Searches SearXNG and GitHub using Malak's implementations
    3. Applies intelligent ranking and filtering
    4. Returns formatted results with source URLs

    Args:
        request: ToolRequest with query

    Returns:
        ToolResult with web search results or error message
    """
    try:
        # Call webguide-service asynchronously
        webguide_response = await search_web_guide(
            query=request.query,
            max_results=10,
        )

        if not webguide_response:
            return ToolResult(
                status=ToolStatus.ERROR,
                tool=ToolName.WEB,
                content="Failed to connect to web guide service. Please ensure webguide-service is running.",
                sources=[],
            )

        # Format the response
        content, sources = format_web_results(webguide_response)

        # Format sources as list of dicts for ToolResult schema
        formatted_sources = [{"url": url, "title": url} for url in sources if url]
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            tool=ToolName.WEB,
            content=content,
            sources=formatted_sources,
        )

    except Exception as e:
        logger.error(f"Error in web_tool: {e}")
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.WEB,
            content=f"Web search error: {str(e)}",
            sources=[],
        )

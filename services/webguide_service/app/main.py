"""
Web Guide Service - FastAPI wrapper for SearXNG and GitHub search.

Exposes Malak's search and ranking functionality as a REST API.
"""

import logging

# Import Malak's implementations
from app.schema.search_result import SearchResult
from app.search.github import GitHubSearchClient, GitHubSearchError
from app.search.ranking import rank_results
from app.search.searxng import SearXNGClient, SearXNGError
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sourcely Web Guide Service",
    version="0.1.0",
    description="Search the web and GitHub repositories with intelligent ranking",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    """Request schema for web search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(
        default=10, ge=1, le=50, description="Maximum results to return"
    )
    sources: list[str] = Field(
        default=["searxng", "github"], description="Search sources to use"
    )
    include_github: bool = Field(
        default=True, description="Include GitHub repository search"
    )


class SearchResponse(BaseModel):
    """Response schema for web search."""

    query: str
    results: list[dict]
    total_results: int
    sources_used: list[str]


@app.get("/")
async def root():
    return {
        "service": "Sourcely Web Guide",
        "status": "running",
        "version": "0.1.0",
        "available_sources": ["searxng", "github"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/search", response_model=SearchResponse)
async def search_web(request: SearchRequest) -> SearchResponse:
    """
    Search the web using SearXNG and optionally GitHub.

    This endpoint:
    1. Searches SearXNG for web results
    2. Optionally searches GitHub for relevant repositories
    3. Ranks and merges results using Malak's ranking algorithm
    4. Returns top-K results with titles, URLs, snippets, and scores

    Args:
        request: SearchRequest with query and options

    Returns:
        SearchResponse with ranked results
    """
    try:
        all_results: list[SearchResult] = []
        sources_used = []

        # Search SearXNG
        if "searxng" in request.sources:
            try:
                searxng_client = SearXNGClient(
                    base_url="http://searxng:8080",  # Docker service name
                    timeout=10.0,
                )
                searxng_results = await searxng_client.search(
                    query=request.query,
                    max_results=request.max_results,
                )
                all_results.extend(searxng_results)
                sources_used.append("searxng")
                logger.info(f"SearXNG returned {len(searxng_results)} results")
            except SearXNGError as e:
                logger.error(f"SearXNG search failed: {e}")

        # Search GitHub
        if "github" in request.sources and request.include_github:
            try:
                github_client = GitHubSearchClient(timeout=10.0)
                github_results = await github_client.search(
                    query=request.query,
                    max_results=min(request.max_results, 10),  # GitHub API limit
                )
                all_results.extend(github_results)
                sources_used.append("github")
                logger.info(f"GitHub returned {len(github_results)} results")
            except GitHubSearchError as e:
                logger.error(f"GitHub search failed: {e}")

        # If no results from any source
        if not all_results:
            return SearchResponse(
                query=request.query,
                results=[],
                total_results=0,
                sources_used=sources_used,
            )

        # Rank and merge results using Malak's ranking algorithm
        ranked_results = rank_results(all_results)

        # Limit to requested max_results
        ranked_results = ranked_results[: request.max_results]

        # Convert to dict format for response
        formatted_results = []
        for result in ranked_results:
            formatted_results.append(
                {
                    "title": result.title,
                    "url": str(result.url),
                    "snippet": result.snippet or "",
                    "source": result.source,
                    "ranking_score": result.ranking_score or 0.0,
                    "published_date": (
                        result.published_date.isoformat()
                        if result.published_date
                        else None
                    ),
                    "stars": result.stars,
                    "language": result.language,
                }
            )

        logger.info(
            f"Returning {len(formatted_results)} ranked results for query: '{request.query}'"
        )

        return SearchResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results),
            sources_used=sources_used,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e!s}",
        )


@app.get("/sources")
async def list_sources():
    """List available search sources and their capabilities."""
    return {
        "sources": [
            {
                "name": "searxng",
                "description": "Privacy-respecting metasearch engine",
                "capabilities": ["web search", "news", "images"],
                "default": True,
            },
            {
                "name": "github",
                "description": "GitHub repository search",
                "capabilities": ["code search", "repository search"],
                "default": True,
            },
        ]
    }

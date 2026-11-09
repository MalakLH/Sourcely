
import asyncio
from typing import Any

from webguide_service.app.search.filtering import filter_results
from webguide_service.app.search.github import GitHubSearchClient
from webguide_service.app.search.ranking import rank_results
from webguide_service.app.search.searxng import SearXNGClient
from webguide_service.app.search.summarizer import OllamaSummarizer
from webguide_service.app.search.url_validator import URLValidator

from app.tools.base import ToolName, ToolRequest, ToolResult, ToolStatus


async def run_web_tool(request: ToolRequest) -> ToolResult:
    """
    Search the web and GitHub, rank and validate results,
    then generate grounded explanations.
    """

    query = request.query.strip()

    if not query:
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.WEB,
            content="The search query cannot be empty.",
            error="Empty search query.",
        )

    # Initialize existing Web Guide components.
    searxng = SearXNGClient(timeout=20.0)
    github = GitHubSearchClient(timeout=20.0)
    validator = URLValidator(timeout=10.0)
    summarizer = OllamaSummarizer(timeout=120.0)

    # Search both sources concurrently.
    search_results = await asyncio.gather(
        searxng.search(query, max_results=10),
        github.search(query, max_results=10),
        return_exceptions=True,
    )

    results = []
    errors = []

    for result in search_results:
        if isinstance(result, BaseException):
            errors.append(str(result))
        else:
            results.extend(result)

    if not results:
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.WEB,
            content="No web results could be retrieved.",
            error="; ".join(errors) or "No results found.",
        )

    # Rank and deduplicate the combined results.
    ranked_results = rank_results(results)

    filtered_results = filter_results(
        ranked_results,
        max_results=5,
    )

    # Validate URLs concurrently.
    validation_results = await asyncio.gather(
        *[
            validator.validate(str(result.url))
            for result in filtered_results
        ],
        return_exceptions=True,
    )

    valid_results = []

    for result, validation in zip(
        filtered_results,
        validation_results, strict=False,
    ):
        if isinstance(validation, BaseException):
            continue

        if validation.is_valid:
            valid_results.append(result)

    if not valid_results:
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.WEB,
            content="Search results were found, but none passed URL validation.",
            error="No valid URLs available.",
        )

    # Generate explanations for validated results.
    summaries = await asyncio.gather(
        *[
            summarizer.summarize(query, result)
            for result in valid_results
        ],
        return_exceptions=True,
    )

    sources: list[dict[str, Any]] = []
    response_lines = ["Here are the most relevant web resources:\n"]

    for result, summary in zip(valid_results, summaries, strict=False):
        if isinstance(summary, BaseException):
            explanation = (
                result.snippet[:300]
                if result.snippet
                else "No explanation available."
            )
        else:
            explanation = summary

        sources.append(
            {
                "title": result.title,
                "url": str(result.url),
                "source": result.source,
                "snippet": result.snippet,
                "explanation": explanation,
                "ranking_score": result.ranking_score,
                "stars": result.stars,
                "language": result.language,
            }
        )

        response_lines.append(
            f"- **{result.title}**\n"
            f"  URL: {result.url}\n"
            f"  Why relevant: {explanation}"
        )

    if errors:
        response_lines.append(
            "\nNote: Some search providers were unavailable."
        )

    return ToolResult(
        status=ToolStatus.SUCCESS,
        tool=ToolName.WEB,
        content="\n\n".join(response_lines),
        sources=sources,
        metadata={
            "query": query,
            "results_found": len(results),
            "results_after_filtering": len(filtered_results),
            "validated_results": len(valid_results),
        },
    )

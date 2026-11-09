import pytest
from app.schema.search_result import SearchResult
from app.search.summarizer import OllamaSummarizer


@pytest.fixture
def summarizer() -> OllamaSummarizer:
    return OllamaSummarizer(
        model="qwen3:4b",
        timeout=120.0,
    )


@pytest.mark.asyncio
async def test_real_fastapi_documentation_summary(summarizer):
    result = SearchResult(
        title="FastAPI Documentation",
        url="https://fastapi.tiangolo.com/",
        snippet=(
            "FastAPI is a modern, fast web framework for building APIs "
            "with Python based on standard Python type hints."
        ),
        source="brave",
    )

    query = "How can I build a REST API using Python?"

    summary = await summarizer.summarize(query, result)

    print("\n========== FASTAPI EXAMPLE ==========")
    print("Query:", query)
    print("Title:", result.title)
    print("Generated explanation:", summary)
    print("=====================================\n")

    assert isinstance(summary, str)
    assert summary.strip()
    assert len(summary.split()) <= 35


@pytest.mark.asyncio
async def test_real_langgraph_repository_summary(summarizer):
    result = SearchResult(
        title="langchain-ai/langgraph",
        url="https://github.com/langchain-ai/langgraph",
        snippet=(
            "Build resilient language agents as graphs. "
            "LangGraph is a library for building stateful, "
            "multi-actor applications with LLMs."
        ),
        source="github",
        stars=1000,
        language="Python",
    )

    query = "Find Python libraries for building multi-agent AI systems."

    summary = await summarizer.summarize(query, result)

    print("\n========== LANGGRAPH EXAMPLE ==========")
    print("Query:", query)
    print("Repository:", result.title)
    print("Generated explanation:", summary)
    print("=======================================\n")

    assert isinstance(summary, str)
    assert summary.strip()
    assert len(summary.split()) <= 35


@pytest.mark.asyncio
async def test_real_summary_with_missing_snippet(summarizer):
    result = SearchResult(
        title="Python Official Documentation",
        url="https://docs.python.org/3/",
        snippet="",
        source="documentation",
    )

    query = "Where can I find Python documentation?"

    summary = await summarizer.summarize(query, result)

    print("\n========== MISSING SNIPPET EXAMPLE ==========")
    print("Query:", query)
    print("Title:", result.title)
    print("Generated explanation:", summary)
    print("=============================================\n")

    assert isinstance(summary, str)
    assert summary.strip()


@pytest.mark.asyncio
async def test_rejects_empty_query(summarizer):
    result = SearchResult(
        title="FastAPI Documentation",
        url="https://fastapi.tiangolo.com/",
        snippet="Documentation for FastAPI.",
        source="documentation",
    )

    with pytest.raises(ValueError, match="Search query cannot be empty"):
        await summarizer.summarize("   ", result)

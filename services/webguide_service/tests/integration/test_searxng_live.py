import pytest
from app.search.searxng import SearXNGClient


@pytest.mark.asyncio
async def test_live_searxng_search():
    client = SearXNGClient(
        base_url="http://localhost:8080",
        timeout=20.0,
    )

    results = await client.search(
        query="FastAPI official documentation",
        max_results=5,
    )

    assert isinstance(results, list)
    assert len(results) > 0
    assert len(results) <= 5

    for result in results:
        assert result.title.strip()
        assert str(result.url).startswith(("http://", "https://"))
        assert result.source
        assert isinstance(result.snippet, str)

    print("\n========== LIVE SEARXNG RESULTS ==========")

    for result in results:
        print(f"\nTitle: {result.title}")
        print(f"URL: {result.url}")
        print(f"Source: {result.source}")
        print(f"Snippet: {result.snippet[:150]}")

    print("\n==========================================")

import pytest
from app.search.github import GitHubSearchClient


@pytest.mark.asyncio
async def test_live_github_repository_search():
    client = GitHubSearchClient(timeout=20.0)

    results = await client.search(
        query="langgraph in:name",
        max_results=5,
    )

    assert isinstance(results, list)
    assert len(results) > 0
    assert len(results) <= 5

    for result in results:
        assert result.title.strip()
        assert "github.com" in str(result.url)
        assert result.source == "github"
        assert result.stars is not None

    print("\n========== LIVE GITHUB RESULTS ==========")

    for result in results:
        print(f"\nRepository: {result.title}")
        print(f"URL: {result.url}")
        print(f"Stars: {result.stars}")
        print(f"Language: {result.language}")
        print(f"Description: {result.snippet}")

    print("\n=========================================")

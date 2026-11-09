import httpx
import pytest
from app.search.github import GitHubSearchClient, GitHubSearchError


@pytest.mark.asyncio
async def test_search_returns_normalized_repositories():
    payload = {
        "items": [
            {
                "full_name": "tiangolo/fastapi",
                "html_url": "https://github.com/tiangolo/fastapi",
                "description": "FastAPI framework.",
                "score": 1.0,
                "updated_at": "2026-10-20T12:00:00Z",
                "stargazers_count": 90000,
                "language": "Python",
            }
        ]
    }

    def handler(request):
        assert request.url.path == "/search/repositories"
        assert request.url.params["q"] == "FastAPI"
        assert request.url.params["per_page"] == "10"

        return httpx.Response(200, json=payload)

    client = GitHubSearchClient(transport=httpx.MockTransport(handler))

    results = await client.search("FastAPI")

    assert len(results) == 1
    assert results[0].title == "tiangolo/fastapi"
    assert results[0].source == "github"
    assert results[0].stars == 90000
    assert results[0].language == "Python"
    assert str(results[0].url) == "https://github.com/tiangolo/fastapi"


@pytest.mark.asyncio
async def test_search_rejects_empty_query():
    client = GitHubSearchClient()

    with pytest.raises(ValueError):
        await client.search("   ")


@pytest.mark.asyncio
async def test_search_rejects_invalid_max_results():
    client = GitHubSearchClient()

    with pytest.raises(ValueError):
        await client.search("FastAPI", max_results=101)


@pytest.mark.asyncio
async def test_search_handles_server_error():
    def handler(request):
        return httpx.Response(503)

    client = GitHubSearchClient(transport=httpx.MockTransport(handler))

    with pytest.raises(GitHubSearchError):
        await client.search("FastAPI")

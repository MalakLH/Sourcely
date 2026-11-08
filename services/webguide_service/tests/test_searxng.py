import httpx
import pytest

from app.search.searxng import SearXNGClient, SearXNGError


@pytest.mark.asyncio
async def test_search_returns_normalized_results():
    payload = {
        "results": [
            {
                "title": "FastAPI Documentation",
                "url": "https://fastapi.tiangolo.com/",
                "content": "Official FastAPI documentation.",
                "engine": "brave",
                "score": 4.0,
            }
        ]
    }

    def handler(request):
        assert request.url.params["q"] == "FastAPI"
        assert request.url.params["format"] == "json"
        return httpx.Response(200, json=payload)

    client = SearXNGClient(transport=httpx.MockTransport(handler))

    results = await client.search("FastAPI")

    assert len(results) == 1
    assert results[0].title == "FastAPI Documentation"
    assert str(results[0].url) == "https://fastapi.tiangolo.com/"
    assert results[0].source == "brave"
    assert results[0].score == 4.0


@pytest.mark.asyncio
async def test_search_rejects_empty_query():
    client = SearXNGClient()

    with pytest.raises(ValueError):
        await client.search("   ")


@pytest.mark.asyncio
async def test_search_rejects_invalid_max_results():
    client = SearXNGClient()

    with pytest.raises(ValueError):
        await client.search("FastAPI", max_results=0)


@pytest.mark.asyncio
async def test_search_handles_server_error():
    def handler(request):
        return httpx.Response(503)

    client = SearXNGClient(transport=httpx.MockTransport(handler))

    with pytest.raises(SearXNGError):
        await client.search("FastAPI")
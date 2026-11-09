import httpx
import pytest
from app.search.url_validator import URLValidator


async def public_resolver(host: str) -> list[str]:
    return ["8.8.8.8"]


@pytest.mark.asyncio
async def test_accepts_reachable_public_url():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    validator = URLValidator(
        transport=httpx.MockTransport(handler),
        resolver=public_resolver,
    )

    result = await validator.validate("https://example.com/docs")

    assert result.is_valid is True
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_rejects_non_http_scheme():
    validator = URLValidator(resolver=public_resolver)

    result = await validator.validate("ftp://example.com/file")

    assert result.is_valid is False
    assert result.reason == "Only HTTP and HTTPS URLs are allowed."


@pytest.mark.asyncio
async def test_rejects_localhost():
    validator = URLValidator(resolver=public_resolver)

    result = await validator.validate("http://localhost:8000/docs")

    assert result.is_valid is False
    assert "Localhost" in result.reason


@pytest.mark.asyncio
async def test_rejects_private_ip_resolution():
    async def private_resolver(host: str) -> list[str]:
        return ["192.168.1.10"]

    validator = URLValidator(resolver=private_resolver)

    result = await validator.validate("https://internal.example.com")

    assert result.is_valid is False
    assert "non-public IP" in result.reason


@pytest.mark.asyncio
async def test_follows_and_validates_redirect():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/start":
            return httpx.Response(
                302,
                headers={"Location": "https://example.com/final"},
            )
        return httpx.Response(200)

    validator = URLValidator(
        transport=httpx.MockTransport(handler),
        resolver=public_resolver,
    )

    result = await validator.validate("https://example.com/start")

    assert result.is_valid is True
    assert result.final_url == "https://example.com/final"


@pytest.mark.asyncio
async def test_rejects_redirect_to_localhost():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"Location": "http://localhost:8000/admin"},
        )

    validator = URLValidator(
        transport=httpx.MockTransport(handler),
        resolver=public_resolver,
    )

    result = await validator.validate("https://example.com/redirect")

    assert result.is_valid is False
    assert "Localhost" in result.reason


@pytest.mark.asyncio
async def test_rejects_too_many_redirects():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"Location": "/another-page"},
        )

    validator = URLValidator(
        max_redirects=1,
        transport=httpx.MockTransport(handler),
        resolver=public_resolver,
    )

    result = await validator.validate("https://example.com/start")

    assert result.is_valid is False
    assert "Maximum redirect count" in result.reason


@pytest.mark.asyncio
async def test_falls_back_to_get_when_head_is_not_supported():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(405)
        return httpx.Response(200)

    validator = URLValidator(
        transport=httpx.MockTransport(handler),
        resolver=public_resolver,
    )

    result = await validator.validate("https://example.com")

    assert result.is_valid is True
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_rejects_not_found_url():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    validator = URLValidator(
        transport=httpx.MockTransport(handler),
        resolver=public_resolver,
    )

    result = await validator.validate("https://example.com/missing")

    assert result.is_valid is False
    assert result.status_code == 404


@pytest.mark.asyncio
async def test_rejects_empty_url():
    validator = URLValidator(resolver=public_resolver)

    result = await validator.validate("   ")

    assert result.is_valid is False
    assert result.reason == "URL cannot be empty."
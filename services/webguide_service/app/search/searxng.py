import httpx

from webguide_service.app.schema.search_result import SearchResult


class SearXNGError(Exception):
    """Raised when the SearXNG search request fails."""


class SearXNGClient:
    """Async client for the local SearXNG instance."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search the web and return normalized results."""

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if max_results < 1:
            raise ValueError("max_results must be at least 1.")

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                transport=self.transport,
            ) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={
                        "q": query.strip(),
                        "format": "json",
                    },
                )
                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as exc:
            raise SearXNGError("SearXNG request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise SearXNGError(
                f"SearXNG returned HTTP {exc.response.status_code}."
            ) from exc
        except httpx.RequestError as exc:
            raise SearXNGError("Could not connect to SearXNG.") from exc
        except ValueError as exc:
            raise SearXNGError("SearXNG returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise SearXNGError("Unexpected SearXNG response format.")

        raw_results = data.get("results", [])

        if not isinstance(raw_results, list):
            raise SearXNGError("Invalid results field in SearXNG response.")

        results: list[SearchResult] = []

        for item in raw_results:
            if not isinstance(item, dict):
                continue

            title = item.get("title")
            url = item.get("url")

            if not isinstance(title, str) or not title.strip():
                continue

            if not isinstance(url, str) or not url.strip():
                continue

            snippet = item.get("content")
            engine = item.get("engine")

            try:
                result = SearchResult(
                    title=title.strip(),
                    url=url,
                    snippet=snippet if isinstance(snippet, str) else "",
                    source=engine if isinstance(engine, str) else "searxng",
                    score=item.get("score"),
                    published_date=item.get("publishedDate"),
                )
                results.append(result)
            except (ValueError, TypeError):
                continue

            if len(results) >= max_results:
                break

        return results
import httpx
from webguide_service.app.schema.search_result import SearchResult


class GitHubSearchError(Exception):
    """Raised when the GitHub repository search fails."""


class GitHubSearchClient:
    """Client for searching public GitHub repositories."""

    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.timeout = timeout
        self.transport = transport

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search GitHub repositories and normalize the results."""

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if not 1 <= max_results <= 100:
            raise ValueError("max_results must be between 1 and 100.")

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                transport=self.transport,
                headers={
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            ) as client:
                response = await client.get(
                    f"{self.BASE_URL}/search/repositories",
                    params={
                        "q": query.strip(),
                        "sort": "updated",
                        "order": "desc",
                        "per_page": max_results,
                    },
                )

                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as exc:
            raise GitHubSearchError("GitHub request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise GitHubSearchError(
                f"GitHub returned HTTP {exc.response.status_code}."
            ) from exc
        except httpx.RequestError as exc:
            raise GitHubSearchError("Could not connect to GitHub.") from exc
        except ValueError as exc:
            raise GitHubSearchError("GitHub returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise GitHubSearchError("Unexpected GitHub response format.")

        repositories = data.get("items", [])

        if not isinstance(repositories, list):
            raise GitHubSearchError("Invalid items field in GitHub response.")

        results: list[SearchResult] = []

        for repo in repositories:
            if not isinstance(repo, dict):
                continue

            name = repo.get("full_name")
            url = repo.get("html_url")

            if not isinstance(name, str) or not name.strip():
                continue

            if not isinstance(url, str) or not url.strip():
                continue

            description = repo.get("description")
            language = repo.get("language")

            try:
                result = SearchResult(
                    title=name,
                    url=url,
                    snippet=description if isinstance(description, str) else "",
                    source="github",
                    score=repo.get("score"),
                    published_date=repo.get("updated_at"),
                    stars=repo.get("stargazers_count"),
                    language=language if isinstance(language, str) else None,
                )
                results.append(result)

            except (ValueError, TypeError):
                continue

            if len(results) >= max_results:
                break

        return results

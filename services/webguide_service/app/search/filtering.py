from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from webguide_service.app.schema.search_result import SearchResult


TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


def _canonicalize_url(url: str) -> str:
    """Normalize URLs to identify duplicate search results."""

    parsed = urlsplit(url)

    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()

    if ":" in host and not host.startswith("["):
        host = f"[{host}]"

    port = parsed.port

    if port and not (
        (scheme == "https" and port == 443)
        or (scheme == "http" and port == 80)
    ):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    path = parsed.path or "/"

    if path != "/":
        path = path.rstrip("/") or "/"

    query_params = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_PARAMS
    ]

    normalized_query = urlencode(query_params)

    return urlunsplit(
        (scheme, netloc, path, normalized_query, "")
    )


def filter_results(
    results: list[SearchResult],
    *,
    max_results: int = 10,
    allowed_sources: set[str] | None = None,
    min_stars: int | None = None,
    language: str | None = None,
) -> list[SearchResult]:
    """
    Filter search results and remove duplicate URLs.

    Results retain their original order. Pass ranked results to this
    function when you want the highest-ranked results to be retained first.
    """

    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    if min_stars is not None and min_stars < 0:
        raise ValueError("min_stars cannot be negative.")

    normalized_sources = (
        {source.casefold() for source in allowed_sources}
        if allowed_sources is not None
        else None
    )

    normalized_language = language.casefold() if language else None

    filtered: list[SearchResult] = []
    seen_urls: set[str] = set()

    for result in results:

        if (
            normalized_sources is not None
            and result.source.casefold() not in normalized_sources
        ):
            continue

        if min_stars is not None:
            if result.stars is None or result.stars < min_stars:
                continue

        if normalized_language is not None:
            if (
                result.language is None
                or result.language.casefold() != normalized_language
            ):
                continue

        canonical_url = _canonicalize_url(str(result.url))

        if canonical_url in seen_urls:
            continue

        seen_urls.add(canonical_url)
        filtered.append(result)

        if len(filtered) >= max_results:
            break

    return filtered
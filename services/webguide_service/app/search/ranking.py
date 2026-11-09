import math
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit

from webguide_service.app.schema.search_result import SearchResult


@dataclass(frozen=True)
class RankingWeights:
    """Weights assigned to each ranking signal."""

    relevance: float = 0.50
    recency: float = 0.20
    domain_quality: float = 0.20
    popularity: float = 0.10

    def __post_init__(self) -> None:
        values = (
            self.relevance,
            self.recency,
            self.domain_quality,
            self.popularity,
        )

        if any(weight < 0 for weight in values):
            raise ValueError("Ranking weights cannot be negative.")

        if not math.isclose(sum(values), 1.0, abs_tol=1e-9):
            raise ValueError("Ranking weights must add up to 1.0.")


OFFICIAL_DOMAINS = {
    "docs.python.org",
    "fastapi.tiangolo.com",
    "developer.mozilla.org",
    "docs.github.com",
    "docs.docker.com",
    "kubernetes.io",
    "cloud.google.com",
    "learn.microsoft.com",
    "docs.aws.amazon.com",
    "docs.langchain.com",
    "pydantic.dev",
}

COMMUNITY_DOMAINS = {
    "stackoverflow.com",
    "readthedocs.io",
}

GITHUB_DOMAIN = "github.com"

STARS_REFERENCE = 100_000
RECENCY_HALF_LIFE_DAYS = 365


def _matches_domain(host: str, domain: str) -> bool:
    """Match a domain and its subdomains without matching lookalikes."""
    return host == domain or host.endswith(f".{domain}")


def _domain_quality(result: SearchResult) -> float:
    """Estimate source quality using a small domain allowlist."""

    host = urlsplit(str(result.url)).hostname

    if not host:
        return 0.5

    host = host.lower().rstrip(".")

    if any(_matches_domain(host, domain) for domain in OFFICIAL_DOMAINS):
        return 1.0

    if _matches_domain(host, GITHUB_DOMAIN):
        return 0.9

    if any(_matches_domain(host, domain) for domain in COMMUNITY_DOMAINS):
        return 0.75

    return 0.5


def _relevance_score(result: SearchResult) -> float:
    """Normalize a non-negative provider score to the 0–1 range."""

    if result.score is None:
        return 0.5

    score = max(result.score, 0.0)
    return score / (score + 1.0)


def _recency_score(
    result: SearchResult,
    now: datetime,
) -> float:
    """Apply exponential decay with a one-year half-life."""

    published = result.published_date

    if published is None:
        return 0.5

    if published.tzinfo is None:
        published = published.replace(tzinfo=UTC)

    age_days = max((now - published).total_seconds() / 86400, 0)

    return 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)


def _popularity_score(result: SearchResult) -> float:
    """Normalize GitHub stars logarithmically."""

    if result.stars is None:
        return 0.5

    stars = max(result.stars, 0)

    return min(
        math.log1p(stars) / math.log1p(STARS_REFERENCE),
        1.0,
    )


def rank_results(
    results: list[SearchResult],
    *,
    now: datetime | None = None,
    weights: RankingWeights | None = None,
) -> list[SearchResult]:
    """Calculate ranking scores and return results from best to worst."""

    current_time = now or datetime.now(UTC)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)

    ranking_weights = weights or RankingWeights()

    ranked_results: list[SearchResult] = []

    for result in results:
        final_score = (
            ranking_weights.relevance * _relevance_score(result)
            + ranking_weights.recency * _recency_score(result, current_time)
            + ranking_weights.domain_quality * _domain_quality(result)
            + ranking_weights.popularity * _popularity_score(result)
        )

        ranked_results.append(
            result.model_copy(
                update={"ranking_score": round(final_score, 4)}
            )
        )

    return sorted(
        ranked_results,
        key=lambda result: result.ranking_score or 0.0,
        reverse=True,
    )
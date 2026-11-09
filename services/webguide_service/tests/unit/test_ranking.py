from datetime import UTC, datetime, timedelta

import pytest
from app.schema.search_result import SearchResult
from app.search.ranking import RankingWeights, rank_results

NOW = datetime(2026, 11, 8, tzinfo=UTC)


def make_result(
    title: str,
    url: str,
    score: float = 1.0,
    published_date: datetime | None = NOW,
    stars: int | None = None,
) -> SearchResult:
    return SearchResult(
        title=title,
        url=url,
        snippet="Test result",
        source="test",
        score=score,
        published_date=published_date,
        stars=stars,
    )


def test_official_documentation_can_outrank_unknown_blog():
    official = make_result(
        "FastAPI Documentation",
        "https://fastapi.tiangolo.com/",
        score=4.0,
    )

    blog = make_result(
        "FastAPI Tutorial",
        "https://random-blog.example.com/",
        score=9.0,
        published_date=NOW - timedelta(days=365),
    )

    results = rank_results([blog, official], now=NOW)

    assert results[0].title == "FastAPI Documentation"
    assert results[0].ranking_score > results[1].ranking_score


def test_recent_results_rank_higher_than_old_results():
    recent = make_result(
        "Recent documentation",
        "https://example.com/recent",
        published_date=NOW,
    )

    old = make_result(
        "Old documentation",
        "https://example.com/old",
        published_date=NOW - timedelta(days=365),
    )

    results = rank_results([old, recent], now=NOW)

    assert results[0].title == "Recent documentation"


def test_github_stars_influence_popularity():
    popular = make_result(
        "Popular repository",
        "https://github.com/example/popular",
        stars=100_000,
    )

    unpopular = make_result(
        "New repository",
        "https://github.com/example/new",
        stars=0,
    )

    results = rank_results([unpopular, popular], now=NOW)

    assert results[0].title == "Popular repository"


def test_missing_metadata_uses_neutral_scores():
    result = make_result(
        "Unknown resource",
        "https://unknown.example.com/",
        score=None,
        published_date=None,
        stars=None,
    )

    ranked = rank_results([result], now=NOW)

    assert ranked[0].ranking_score == 0.5


def test_original_provider_score_is_preserved():
    result = make_result(
        "FastAPI",
        "https://fastapi.tiangolo.com/",
        score=4.0,
    )

    ranked = rank_results([result], now=NOW)

    assert ranked[0].score == 4.0
    assert ranked[0].ranking_score is not None


def test_invalid_ranking_weights_are_rejected():
    with pytest.raises(ValueError):
        RankingWeights(
            relevance=0.5,
            recency=0.3,
            domain_quality=0.3,
            popularity=0.1,
        )

import pytest
from app.schema.search_result import SearchResult
from app.search.filtering import filter_results


def make_result(
    title: str,
    url: str,
    source: str = "brave",
    stars: int | None = None,
    language: str | None = None,
) -> SearchResult:
    return SearchResult(
        title=title,
        url=url,
        snippet="Test result",
        source=source,
        stars=stars,
        language=language,
    )


def test_removes_duplicate_urls():
    results = [
        make_result("First", "https://example.com/docs"),
        make_result("Duplicate", "https://example.com/docs"),
    ]

    filtered = filter_results(results)

    assert len(filtered) == 1
    assert filtered[0].title == "First"


def test_removes_tracking_parameters_when_detecting_duplicates():
    results = [
        make_result(
            "First",
            "https://example.com/docs?utm_source=google",
        ),
        make_result(
            "Duplicate",
            "https://example.com/docs",
        ),
    ]

    filtered = filter_results(results)

    assert len(filtered) == 1


def test_filters_by_source():
    results = [
        make_result("Web result", "https://example.com"),
        make_result(
            "GitHub repository",
            "https://github.com/example/project",
            source="github",
        ),
    ]

    filtered = filter_results(
        results,
        allowed_sources={"github"},
    )

    assert len(filtered) == 1
    assert filtered[0].source == "github"


def test_filters_by_minimum_stars():
    results = [
        make_result(
            "Small repository",
            "https://github.com/example/small",
            source="github",
            stars=10,
        ),
        make_result(
            "Popular repository",
            "https://github.com/example/popular",
            source="github",
            stars=1000,
        ),
    ]

    filtered = filter_results(results, min_stars=100)

    assert len(filtered) == 1
    assert filtered[0].stars == 1000


def test_filters_by_programming_language():
    results = [
        make_result(
            "Python project",
            "https://github.com/example/python",
            source="github",
            language="Python",
        ),
        make_result(
            "JavaScript project",
            "https://github.com/example/javascript",
            source="github",
            language="JavaScript",
        ),
    ]

    filtered = filter_results(results, language="python")

    assert len(filtered) == 1
    assert filtered[0].language == "Python"


def test_respects_max_results():
    results = [
        make_result("First", "https://example.com/1"),
        make_result("Second", "https://example.com/2"),
        make_result("Third", "https://example.com/3"),
    ]

    filtered = filter_results(results, max_results=2)

    assert len(filtered) == 2


def test_rejects_invalid_max_results():
    with pytest.raises(ValueError):
        filter_results([], max_results=0)


def test_rejects_negative_min_stars():
    with pytest.raises(ValueError):
        filter_results([], min_stars=-1)
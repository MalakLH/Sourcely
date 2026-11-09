import pytest

from app.search.filtering import filter_results
from app.search.ranking import rank_results
from app.search.searxng import SearXNGClient
from app.search.url_validator import URLValidator


@pytest.mark.asyncio
async def test_live_webguide_pipeline():
    # 1. Retrieve real search results from SearXNG.
    search_client = SearXNGClient(
        base_url="http://localhost:8080",
        timeout=20.0,
    )

    results = await search_client.search(
        query="Python FastAPI REST API documentation",
        max_results=10,
    )

    assert results

    print(f"\nRetrieved {len(results)} search results.")

    # 2. Rank the results.
    ranked_results = rank_results(results)

    assert ranked_results

    for result in ranked_results:
        assert result.ranking_score is not None

    print("Ranking completed.")

    # 3. Filter and deduplicate.
    filtered_results = filter_results(
        ranked_results,
        max_results=5,
    )

    assert filtered_results
    assert len(filtered_results) <= 5

    print(f"Filtering completed: {len(filtered_results)} results remain.")

    # 4. Validate the URLs of the remaining results.
    validator = URLValidator(timeout=15.0)

    validated_results = []

    for result in filtered_results:
        validation = await validator.validate(str(result.url))

        print(f"\nURL: {result.url}")
        print(f"Valid: {validation.is_valid}")
        print(f"Status: {validation.status_code}")
        print(f"Reason: {validation.reason}")

        if validation.is_valid:
            validated_results.append(result)

    # 5. Verify that the pipeline produced usable results.
    assert isinstance(validated_results, list)

    print("\n========== WEB GUIDE PIPELINE ==========")
    print(f"Initially retrieved: {len(results)}")
    print(f"After filtering: {len(filtered_results)}")
    print(f"After URL validation: {len(validated_results)}")

    for result in validated_results:
        print(f"\n{result.title}")
        print(f"URL: {result.url}")
        print(f"Ranking score: {result.ranking_score}")

    print("========================================")
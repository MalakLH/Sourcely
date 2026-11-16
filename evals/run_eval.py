#!/usr/bin/env python3
"""
Evaluation script for Docs Expert RAG system.

Computes metrics:
- Retrieval Hit Rate@K: Percentage of queries where at least one expected source is retrieved
- Citation Validity: Percentage of citations that match actual retrieved sources
- Average Similarity Score: Mean similarity score across all retrievals
- Confidence Distribution: Distribution of confidence levels (high/medium/low)
"""

import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx


@dataclass
class EvalMetrics:
    """Container for evaluation metrics."""

    total_queries: int
    successful_queries: int
    failed_queries: int
    hit_rate: float
    avg_similarity_score: float
    avg_retrieved_count: float
    confidence_distribution: dict[str, int]
    category_performance: dict[str, dict]


class DocsEvaluator:
    """Evaluator for the Docs Expert RAG system."""

    def __init__(self, docs_service_url: str = "http://localhost:8001"):
        self.docs_service_url = docs_service_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def retrieve(self, query: str, top_k: int = 5) -> Optional[dict]:
        """Call the docs-service /retrieve endpoint."""
        try:
            response = await self.client.post(
                f"{self.docs_service_url}/retrieve",
                json={"query": query, "top_k": top_k},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error retrieving for query '{query}': {e}")
            return None

    def calculate_hit_rate(
        self,
        retrieval_response: dict,
        expected_sources_contain: list[str],
    ) -> bool:
        """
        Check if at least one expected source keyword appears in retrieved sources.

        Args:
            retrieval_response: Response from /retrieve endpoint
            expected_sources_contain: List of keywords that should appear in sources

        Returns:
            True if hit (at least one keyword found), False otherwise
        """
        if not retrieval_response or not retrieval_response.get("results"):
            return False

        # Get all source URLs from results
        sources = [
            result.get("source_url", "").lower()
            for result in retrieval_response["results"]
        ]

        # Check if any expected keyword appears in any source
        for keyword in expected_sources_contain:
            keyword_lower = keyword.lower()
            if any(keyword_lower in source for source in sources):
                return True

        return False

    def check_keyword_presence(
        self,
        retrieval_response: dict,
        expected_keywords: list[str],
    ) -> dict:
        """
        Check how many expected keywords appear in retrieved content.

        Args:
            retrieval_response: Response from /retrieve endpoint
            expected_keywords: List of keywords expected in results

        Returns:
            Dict with keyword coverage statistics
        """
        if not retrieval_response or not retrieval_response.get("results"):
            return {"found": 0, "total": len(expected_keywords), "coverage": 0.0}

        # Combine all retrieved content
        all_content = " ".join(
            result.get("content", "").lower()
            for result in retrieval_response["results"]
        )

        # Count how many keywords are present
        found_keywords = sum(
            1 for keyword in expected_keywords if keyword.lower() in all_content
        )

        coverage = found_keywords / len(expected_keywords) if expected_keywords else 0.0

        return {
            "found": found_keywords,
            "total": len(expected_keywords),
            "coverage": coverage,
        }

    async def evaluate_test_case(self, test_case: dict) -> dict:
        """
        Evaluate a single test case.

        Args:
            test_case: Test case from golden dataset

        Returns:
            Evaluation results for this test case
        """
        query = test_case["question"]
        expected_sources_contain = test_case.get("expected_sources_contain", [])
        expected_keywords = test_case.get("expected_keywords", [])

        # Retrieve documents
        retrieval_response = await self.retrieve(query, top_k=5)

        if not retrieval_response:
            return {
                "test_id": test_case["id"],
                "category": test_case["category"],
                "success": False,
                "hit": False,
                "similarity_score": 0.0,
                "retrieved_count": 0,
                "confidence": "none",
                "keyword_coverage": 0.0,
            }

        # Calculate metrics
        hit = self.calculate_hit_rate(retrieval_response, expected_sources_contain)

        results = retrieval_response.get("results", [])
        avg_similarity = (
            sum(r.get("similarity_score", 0.0) for r in results) / len(results)
            if results
            else 0.0
        )

        keyword_check = self.check_keyword_presence(retrieval_response, expected_keywords)

        return {
            "test_id": test_case["id"],
            "category": test_case["category"],
            "difficulty": test_case.get("difficulty", "unknown"),
            "success": True,
            "hit": hit,
            "similarity_score": avg_similarity,
            "retrieved_count": len(results),
            "confidence": retrieval_response.get("confidence", "unknown"),
            "keyword_coverage": keyword_check["coverage"],
            "keywords_found": keyword_check["found"],
            "keywords_total": keyword_check["total"],
        }

    async def run_evaluation(self, dataset_path: Path) -> EvalMetrics:
        """
        Run evaluation on the golden dataset.

        Args:
            dataset_path: Path to golden_dataset.json

        Returns:
            EvalMetrics with overall results
        """
        # Load dataset
        with open(dataset_path) as f:
            dataset = json.load(f)

        test_cases = dataset["test_cases"]
        print(f"\nRunning evaluation on {len(test_cases)} test cases...\n")

        # Evaluate all test cases
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] Evaluating: {test_case['id']}")
            result = await self.evaluate_test_case(test_case)
            results.append(result)

        # Calculate aggregate metrics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        hits = [r for r in successful if r["hit"]]
        hit_rate = len(hits) / len(successful) if successful else 0.0

        avg_similarity = (
            sum(r["similarity_score"] for r in successful) / len(successful)
            if successful
            else 0.0
        )

        avg_retrieved = (
            sum(r["retrieved_count"] for r in successful) / len(successful)
            if successful
            else 0.0
        )

        # Confidence distribution
        confidence_dist = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
        for r in successful:
            conf = r.get("confidence", "unknown")
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1

        # Category performance
        category_perf = {}
        for r in successful:
            cat = r["category"]
            if cat not in category_perf:
                category_perf[cat] = {
                    "total": 0,
                    "hits": 0,
                    "avg_similarity": 0.0,
                    "avg_keyword_coverage": 0.0,
                }

            category_perf[cat]["total"] += 1
            if r["hit"]:
                category_perf[cat]["hits"] += 1
            category_perf[cat]["avg_similarity"] += r["similarity_score"]
            category_perf[cat]["avg_keyword_coverage"] += r["keyword_coverage"]

        # Finalize category averages
        for cat, perf in category_perf.items():
            total = perf["total"]
            perf["hit_rate"] = perf["hits"] / total if total > 0 else 0.0
            perf["avg_similarity"] /= total if total > 0 else 1
            perf["avg_keyword_coverage"] /= total if total > 0 else 1

        metrics = EvalMetrics(
            total_queries=len(test_cases),
            successful_queries=len(successful),
            failed_queries=len(failed),
            hit_rate=hit_rate,
            avg_similarity_score=avg_similarity,
            avg_retrieved_count=avg_retrieved,
            confidence_distribution=confidence_dist,
            category_performance=category_perf,
        )

        return metrics

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def print_metrics(metrics: EvalMetrics) -> None:
    """Pretty print evaluation metrics."""
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)

    print(f"\nOverall Performance:")
    print(f"  Total Queries:      {metrics.total_queries}")
    print(f"  Successful:         {metrics.successful_queries}")
    print(f"  Failed:             {metrics.failed_queries}")
    print(f"  Hit Rate@5:         {metrics.hit_rate:.2%}")
    print(f"  Avg Similarity:     {metrics.avg_similarity_score:.4f}")
    print(f"  Avg Retrieved:      {metrics.avg_retrieved_count:.2f}")

    print(f"\nConfidence Distribution:")
    for conf, count in sorted(metrics.confidence_distribution.items()):
        percentage = (
            count / metrics.successful_queries * 100 if metrics.successful_queries > 0 else 0
        )
        print(f"  {conf.capitalize():10s}: {count:3d} ({percentage:5.1f}%)")

    print(f"\nPerformance by Category:")
    print(f"  {'Category':<25s} {'Hit Rate':>10s} {'Avg Sim':>10s} {'Kw Cov':>10s} {'Count':>8s}")
    print(f"  {'-' * 25} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 8}")

    for cat, perf in sorted(metrics.category_performance.items()):
        print(
            f"  {cat:<25s} "
            f"{perf['hit_rate']:>9.1%} "
            f"{perf['avg_similarity']:>10.4f} "
            f"{perf['avg_keyword_coverage']:>9.1%} "
            f"{perf['total']:>8d}"
        )

    print("\n" + "=" * 70)

    # Overall grade
    if metrics.hit_rate >= 0.9:
        grade = "EXCELLENT"
    elif metrics.hit_rate >= 0.75:
        grade = "GOOD"
    elif metrics.hit_rate >= 0.6:
        grade = "ACCEPTABLE"
    else:
        grade = "NEEDS IMPROVEMENT"

    print(f"\nOverall Grade: {grade}")
    print("=" * 70 + "\n")


async def main():
    """Main evaluation entry point."""
    # Get dataset path
    dataset_path = Path(__file__).parent / "golden_dataset.json"

    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        sys.exit(1)

    # Check if docs-service is available
    docs_service_url = "http://localhost:8001"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{docs_service_url}/health")
            response.raise_for_status()
            print(f"✓ Connected to docs-service at {docs_service_url}")
    except Exception as e:
        print(f"✗ Cannot connect to docs-service at {docs_service_url}")
        print(f"  Error: {e}")
        print("\nPlease ensure docs-service is running:")
        print("  cd services/docs_service")
        print("  uvicorn app.main:app --port 8001")
        sys.exit(1)

    # Run evaluation
    evaluator = DocsEvaluator(docs_service_url)
    try:
        metrics = await evaluator.run_evaluation(dataset_path)
        print_metrics(metrics)

        # Save results to file
        results_path = Path(__file__).parent / "eval_results.json"
        with open(results_path, "w") as f:
            json.dump(
                {
                    "total_queries": metrics.total_queries,
                    "successful_queries": metrics.successful_queries,
                    "failed_queries": metrics.failed_queries,
                    "hit_rate": metrics.hit_rate,
                    "avg_similarity_score": metrics.avg_similarity_score,
                    "avg_retrieved_count": metrics.avg_retrieved_count,
                    "confidence_distribution": metrics.confidence_distribution,
                    "category_performance": metrics.category_performance,
                },
                f,
                indent=2,
            )
        print(f"Results saved to: {results_path}")

    finally:
        await evaluator.close()


if __name__ == "__main__":
    asyncio.run(main())

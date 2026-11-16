# Docs Expert RAG Evaluation Harness

This directory contains the evaluation framework for measuring the performance of the Docs Expert RAG system.

## Contents

- **golden_dataset.json**: 52 question-answer pairs covering Kubernetes concepts (Pods, Services, Deployments)
- **run_eval.py**: Python script that evaluates retrieval performance
- **eval_results.json**: Generated results file (created after running evaluation)

## Metrics

The evaluation computes the following metrics:

### Retrieval Hit Rate@K
Percentage of queries where at least one expected source document is retrieved in the top-K results.

### Average Similarity Score
Mean cosine similarity score across all retrieved documents.

### Keyword Coverage
Percentage of expected keywords found in retrieved content.

### Confidence Distribution
Distribution of confidence levels (high/medium/low) assigned by the system.

### Category Performance
Breakdown of performance by question category (pods_basics, services_types, deployments_use_cases, etc.)

## Usage

### Prerequisites

1. Ensure docs-service is running:
```bash
cd services/docs_service
uvicorn app.main:app --port 8001
```

2. Ensure K8s documentation is ingested:
```bash
# Using curl or httpx
curl -X POST http://localhost:8001/ingest/k8s
```

### Running the Evaluation

```bash
cd evals
python run_eval.py
```

### Expected Output

```
✓ Connected to docs-service at http://localhost:8001

Running evaluation on 52 test cases...

[1/52] Evaluating: k8s-001
[2/52] Evaluating: k8s-002
...

======================================================================
EVALUATION RESULTS
======================================================================

Overall Performance:
  Total Queries:      52
  Successful:         52
  Failed:             0
  Hit Rate@5:         92.31%
  Avg Similarity:     0.7234
  Avg Retrieved:      5.00

Confidence Distribution:
  High:       35 ( 67.3%)
  Medium:     14 ( 26.9%)
  Low:         3 (  5.8%)

Performance by Category:
  Category                    Hit Rate    Avg Sim     Kw Cov    Count
  ------------------------- ---------- ---------- ---------- --------
  deployments_basics             95.0%     0.7456     87.5%        8
  pods_basics                   100.0%     0.7823     92.3%       10
  services_types                 88.9%     0.6891     81.2%       12
  ...

======================================================================

Overall Grade: EXCELLENT
======================================================================
```

## Golden Dataset Structure

Each test case includes:

```json
{
  "id": "k8s-001",
  "category": "pods_basics",
  "question": "What is a Pod in Kubernetes?",
  "expected_keywords": ["smallest deployable unit", "group of containers"],
  "expected_sources_contain": ["pods"],
  "difficulty": "easy"
}
```

## Extending the Dataset

To add new test cases:

1. Open `golden_dataset.json`
2. Add a new entry to the `test_cases` array
3. Follow the existing structure
4. Update the `total_questions` count in metadata
5. Run evaluation to validate

## Interpreting Results

### Hit Rate@5
- **>90%**: Excellent retrieval quality
- **75-90%**: Good retrieval quality
- **60-75%**: Acceptable, may need tuning
- **<60%**: Poor, requires investigation

### Similarity Score
- **>0.7**: Strong semantic match
- **0.5-0.7**: Moderate match
- **<0.5**: Weak match, may indicate poor results

### Keyword Coverage
- **>80%**: Retrieved content contains most expected information
- **50-80%**: Partial coverage, answer may be incomplete
- **<50%**: Poor coverage, retrieval likely missed key information

## Troubleshooting

### Connection Error
```
✗ Cannot connect to docs-service at http://localhost:8001
```
**Solution**: Start the docs-service using `uvicorn app.main:app --port 8001`

### Low Hit Rate
- Check if documentation is properly ingested
- Verify embedding model is loaded correctly
- Review chunk size and overlap settings
- Examine failed test cases for patterns

### Low Similarity Scores
- May indicate mismatch between query and document embeddings
- Consider using a different embedding model
- Review chunking strategy (headings, overlap)

## Future Enhancements

- [ ] Add faithfulness scoring (LLM-as-judge)
- [ ] Add answer relevance metrics
- [ ] Support for multi-hop reasoning questions
- [ ] Adversarial test cases
- [ ] Performance benchmarking (latency, throughput)

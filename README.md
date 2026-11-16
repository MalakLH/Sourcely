# Sourcely: AI Developer Agent

Sourcely is an AI-powered developer assistant that provides intelligent code analysis, documentation search, and security scanning capabilities.

## Architecture

Sourcely is built as a modular monorepo with multiple microservices:

- **Agent Service** (`:8000`): LangGraph-based orchestration and routing
- **Docs Service** (`:8001`): RAG system for documentation retrieval with LanceDB
- **Scanner Service** (`:8002`): Code security scanning with Bandit and Semgrep
- **Web Guide Service** (planned): SearXNG + GitHub search integration

## Features

### 1. Docs Expert RAG System ✅

- **Heading-Aware Chunking**: Intelligently chunks documentation by H1/H2/H3 headings with 12.5% overlap
- **Vector Search**: Uses sentence-transformers and LanceDB for semantic retrieval
- **LLM-Grounded Answers**: Ollama generates answers strictly from retrieved context with citations
- **Confidence Scoring**: Automatic confidence assessment (high/medium/low)
- **Multi-Source Documentation**: Kubernetes, Python, and Docker documentation indexed
- **Evaluation Framework**: Golden dataset with 52 K8s Q&A pairs for measuring retrieval quality

### 2. Code Scanner Service ✅

- **Multi-Scanner Support**: Runs Bandit (Python) and Semgrep (multi-language)
- **Unified Schema**: Normalizes findings from different scanners
- **LLM Explanations**: Generates plain-English remediation advice using Ollama
- **Severity Mapping**: Consistent LOW/MEDIUM/HIGH/CRITICAL classification

### 3. Web Guide Service ✅

- **SearXNG Integration**: Privacy-respecting metasearch engine
- **GitHub Search**: Repository search with star counts and language metadata
- **Intelligent Ranking**: Malak's ranking algorithm (relevance, recency, domain quality, popularity)
- **Unified Results**: Merged and ranked results from multiple sources

### 4. Agent Orchestration ✅

- **LangGraph Workflow**: State-based routing to specialized tools
- **Tool Integration**: Seamless communication between agent and microservices
- **Fallback Logic**: Automatic fallback (Docs → Web Guide)

### 5. Streamlit UI ✅

- **Chat Interface**: Interactive conversation with the agent
- **Code Scanner**: Visual code editor with security vulnerability scanning
- **Real-time Results**: Live updates with syntax highlighting
- **Service Monitoring**: Health checks and documentation statistics

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- [Ollama](https://ollama.ai) installed locally
- (Optional) Git for version control

### 1. Install Ollama Models

```bash
# For agent service (general purpose)
ollama pull qwen3:4b

# For scanner explanations (code-focused)
ollama pull qwen2.5-coder:3b
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and configure:
# - OLLAMA_BASE_URL (default: http://localhost:11434)
# - SEARXNG_SECRET (generate random string)
```

### 3. Start Services with Docker Compose

```bash
cd infrastructure/docker
docker-compose up -d
```

This starts:
- `agent-service` on port 8000
- `docs-service` on port 8001
- `scanner-service` on port 8002
- `webguide-service` on port 8003
- `ui-service` on port 8501 (Streamlit)
- `searxng` on port 8080

### 4. Ingest Documentation

```bash
# Ingest all documentation (Kubernetes, Python, Docker)
curl -X POST http://localhost:8001/ingest/all

# Check ingestion stats
curl http://localhost:8001/stats
```

### 5. Access the UI

Open your browser to: **http://localhost:8501**

Or test the agent directly:

```bash
# Query documentation
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a Kubernetes Pod?"}'

# Scan code for vulnerabilities
curl -X POST http://localhost:8002/scan \
  -H "Content-Type: application/json" \
  -d '{
    "code": "password = \"hardcoded123\"",
    "language": "python",
    "scanners": ["bandit"]
  }'
```

### 6. Verify Integration

```bash
# Run integration tests
python scripts/verify_integration.py
```

## Development Setup

### Install Individual Services

#### Agent Service

```bash
cd services/agent_services
pip install -e ".[dev]"
uvicorn app.main:app --port 8000 --reload
```

#### Docs Service

```bash
cd services/docs_service
pip install -e ".[dev]"
uvicorn app.main:app --port 8001 --reload
```

#### Scanner Service

```bash
cd services/scanner_service
pip install -e ".[dev]"

# Install scanner dependencies
pip install bandit semgrep

uvicorn app.main:app --port 8002 --reload
```

### Running Tests

```bash
# Test docs service
cd services/docs_service
pytest -v

# Test scanner service
cd services/scanner_service
pytest -v

# Test agent service
cd services/agent_services
pytest -v
```

### Running Evaluation

```bash
# Ensure docs-service is running and data is ingested
cd evals
python run_eval.py
```

## API Documentation

### Agent Service (`:8000`)

- `GET /` - Service info
- `POST /api/query` - Submit query to agent
- `GET /health` - Health check

### Docs Service (`:8001`)

- `POST /retrieve` - Retrieve documentation chunks
  ```json
  {
    "query": "What are Kubernetes Pods?",
    "top_k": 5,
    "similarity_threshold": 0.3
  }
  ```

- `POST /ingest/k8s` - Ingest Kubernetes documentation
- `POST /ingest/all` - Ingest all documentation (K8s, Python, Docker)
- `GET /stats` - Vector store statistics
- `DELETE /clear` - Clear vector store

### Scanner Service (`:8002`)

- `POST /scan` - Scan code for vulnerabilities
  ```json
  {
    "code": "eval(user_input)",
    "language": "python",
    "scanners": ["bandit", "semgrep"],
    "include_explanations": false
  }
  ```

- `POST /explain` - Generate LLM explanation for a finding
- `GET /scanners` - List available scanners
- `GET /severity-levels` - List severity levels

### Web Guide Service (`:8003`)

- `POST /search` - Search web and GitHub
  ```json
  {
    "query": "Docker best practices",
    "max_results": 10,
    "sources": ["searxng", "github"]
  }
  ```

- `GET /sources` - List available search sources

### UI Service (`:8501`)

- Access via browser: http://localhost:8501
- **Chat Tab**: Interactive agent conversation
- **Scanner Tab**: Code security analysis with visual editor

## Project Structure

```
Sourcely/
├── services/
│   ├── agent_services/       # LangGraph agent orchestration
│   │   ├── app/
│   │   │   ├── agent/        # Graph, router, state
│   │   │   ├── tools/        # Tool implementations
│   │   │   └── schemas/      # Request/response models
│   │   └── tests/
│   ├── docs_service/         # RAG documentation system
│   │   ├── app/
│   │   │   ├── ingestion/    # Chunking, embedding, pipeline
│   │   │   ├── api/          # FastAPI routes
│   │   │   └── models/       # Pydantic schemas
│   │   ├── data/
│   │   │   ├── raw/          # Source documentation
│   │   │   └── vectordb/     # LanceDB storage
│   │   └── tests/
│   ├── scanner_service/      # Code security scanning
│   │   ├── app/
│   │   │   ├── scanners/     # Bandit, Semgrep, LLM explainer
│   │   │   ├── api/          # FastAPI routes
│   │   │   └── models/       # Scan schemas
│   │   └── tests/
│   └── webguide_service/     # SearXNG + GitHub (partial)
├── evals/                    # Evaluation framework
│   ├── golden_dataset.json   # 52 K8s Q&A test cases
│   ├── run_eval.py          # Evaluation script
│   └── README.md
├── infrastructure/
│   └── docker/
│       ├── docker-compose.yml
│       └── searxng/
├── docs/adr/                 # Architecture Decision Records
└── .github/workflows/        # CI/CD pipelines
```

## Technology Stack

### Core Frameworks
- **FastAPI**: REST API framework for all services
- **LangGraph**: Agent workflow orchestration
- **LangChain**: LLM abstractions and integrations

### LLM & Embeddings
- **Ollama**: Local LLM inference (qwen3:4b, qwen2.5-coder:3b)
- **sentence-transformers**: Text embeddings (all-MiniLM-L6-v2)

### Vector Storage
- **LanceDB**: Embedded vector database for RAG

### Security Scanners
- **Bandit**: Python security linter
- **Semgrep**: Multi-language static analysis

### Search
- **SearXNG**: Privacy-respecting metasearch engine
- **GitHub API**: Repository search

## Configuration

Key environment variables in `.env`:

```bash
# Application
APP_NAME=Sourcely
APP_ENV=development

# Ollama LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
OLLAMA_TEMPERATURE=0

# Services
DOCS_SERVICE_URL=http://localhost:8001

# Search
SEARXNG_BASE_URL=http://localhost:8080
SEARXNG_SECRET=your_random_secret_here
```

## Evaluation Metrics

The `evals/` framework measures:

- **Retrieval Hit Rate@K**: % of queries with expected source in top-K
- **Average Similarity Score**: Mean cosine similarity of retrieved chunks
- **Keyword Coverage**: % of expected keywords found in results
- **Confidence Distribution**: Distribution of high/medium/low confidence

Target performance:
- Hit Rate@5: >90% (Excellent), >75% (Good)
- Avg Similarity: >0.7 (Strong match)
- Keyword Coverage: >80% (Complete)

## Architecture Decisions

See `docs/adr/` for detailed rationale:

- **ADR 001**: Monorepo and Modular Monolith
- **ADR 002**: Local LLM with Ollama
- **ADR 003**: LangGraph for Agent Orchestration

## Roadmap

### Week 1-2 (Completed ✅)
- [x] Agent service skeleton with LangGraph
- [x] Docs Expert RAG with LanceDB
- [x] Code scanner with Bandit/Semgrep
- [x] Evaluation framework
- [x] Web Guide service integration
- [x] Streamlit UI with chat and scanner
- [x] Multi-source documentation (K8s, Python, Docker)

### Week 3-4 (In Progress)
- [ ] Sandbox execution service
- [ ] Ledger service (hash-chained audit log)

### Week 5-6 (Planned)
- [ ] Kubernetes deployment (k3s/Helm)
- [ ] Observability (LangFuse, Prometheus)
- [ ] Production hardening

## Contributing

### Code Style
- Python: Ruff (line length 100)
- Type hints required
- Pydantic models for all schemas

### Testing
- Pytest for unit tests
- `pytest-asyncio` for async tests
- Minimum 70% coverage

### Commits
- Conventional commits format
- Keep commits focused and atomic

## License

This project is for educational and research purposes.

## Team

- **Malak**: Infrastructure, Agent Service, Web Guide, Sandbox, K8s, CI/CD
- **Eya**: Docs Expert RAG, Scanner Service, Evaluation Framework

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review ADRs for architecture decisions
3. Consult service-specific READMEs

---

**Status**: Active Development  
**Version**: 0.1.0  
**Last Updated**: November 8, 2026

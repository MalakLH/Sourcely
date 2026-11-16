# Sourcely Integration Guide

## Complete Setup and Integration Instructions

This guide walks you through setting up all Sourcely services and verifying end-to-end integration.

---

## Prerequisites

### Required Software
- **Docker** and **Docker Compose**
- **Ollama** with models: `qwen3:4b` and `qwen2.5-coder:3b`
- **Python 3.11+** (for local development)
- **Git**

### Install Ollama Models

```bash
# For agent and docs service
ollama pull qwen3:4b

# For scanner explanations
ollama pull qwen2.5-coder:3b
```

---

## Quick Start (Docker Compose)

### 1. Clone and Configure

```bash
cd Sourcely

# Copy environment template
cp .env.example .env

# Edit .env and set SEARXNG_SECRET to a random string
nano .env  # or use your favorite editor
```

### 2. Start All Services

```bash
cd infrastructure/docker
docker-compose up -d
```

This starts:
- **agent-service** (`:8000`) - LangGraph orchestration
- **docs-service** (`:8001`) - RAG documentation search
- **scanner-service** (`:8002`) - Code security scanning
- **webguide-service** (`:8003`) - Web & GitHub search
- **ui-service** (`:8501`) - Streamlit interface
- **searxng** (`:8080`) - Privacy-respecting search engine

### 3. Verify Services

```bash
# Check all containers are running
docker-compose ps

# Check logs
docker-compose logs -f

# Health checks
curl http://localhost:8000/health  # agent
curl http://localhost:8001/health  # docs
curl http://localhost:8002/health  # scanner
curl http://localhost:8003/health  # webguide
```

### 4. Ingest Documentation

```bash
# Ingest all documentation (K8s, Python, Docker)
curl -X POST http://localhost:8001/ingest/all

# Check ingestion stats
curl http://localhost:8001/stats
```

Expected output:
```json
{
  "service": "Sourcely Docs Expert",
  "vector_store": {
    "exists": true,
    "count": 50+,
    "table_name": "kubernetes_docs"
  },
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### 5. Access UI

Open your browser to: **http://localhost:8501**

---

## Service-by-Service Testing

### Agent Service (`:8000`)

The agent routes queries to appropriate tools based on content.

```bash
# Test documentation query (routes to docs-service)
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a Kubernetes Pod?"}'

# Test web search query (routes to webguide-service)
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find GitHub repositories about FastAPI"}'
```

### Docs Service (`:8001`)

RAG-based documentation retrieval with LLM-grounded answers.

```bash
# Retrieve documentation chunks
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I create a Deployment in Kubernetes?",
    "top_k": 5
  }'

# Ingest Kubernetes docs only
curl -X POST http://localhost:8001/ingest/k8s

# Clear vector store
curl -X DELETE http://localhost:8001/clear
```

### Scanner Service (`:8002`)

Security scanning with Bandit and Semgrep.

```bash
# Scan Python code
curl -X POST http://localhost:8002/scan \
  -H "Content-Type: application/json" \
  -d '{
    "code": "password = \"hardcoded123\"\neval(user_input)",
    "language": "python",
    "scanners": ["bandit"],
    "include_explanations": false
  }'

# Get LLM explanation for a finding
curl -X POST http://localhost:8002/explain \
  -H "Content-Type: application/json" \
  -d '{
    "finding": {
      "file": "test.py",
      "line": 1,
      "rule_id": "B105",
      "severity": "MEDIUM",
      "description": "Hardcoded password string",
      "scanner": "bandit"
    }
  }'

# List available scanners
curl http://localhost:8002/scanners
```

### Web Guide Service (`:8003`)

Web and GitHub search with intelligent ranking.

```bash
# Search web and GitHub
curl -X POST http://localhost:8003/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Docker best practices",
    "max_results": 10,
    "sources": ["searxng", "github"]
  }'

# List available sources
curl http://localhost:8003/sources
```

---

## UI Service Features

### Chat Interface Tab

1. **Ask Questions:**
   - "What is a Kubernetes Service?"
   - "How do I use Python asyncio?"
   - "Find Docker networking tutorials"

2. **View Results:**
   - LLM-grounded answers
   - Numbered citations with source URLs
   - Confidence scores (high/medium/low)
   - Tool used indicator

3. **Chat History:**
   - Maintains conversation context
   - Clear history button in sidebar

### Code Scanner Tab

1. **Paste Code:**
   - Use the embedded code editor
   - Supports multiple languages

2. **Configure Scan:**
   - Select language (Python, JavaScript, etc.)
   - Choose scanners (Bandit, Semgrep)
   - Toggle LLM explanations

3. **View Results:**
   - Findings grouped by severity
   - Code snippets highlighted
   - AI-generated explanations
   - Remediation advice

4. **Severity Levels:**
   - 🔴 CRITICAL
   - 🟠 HIGH
   - 🟡 MEDIUM
   - 🟢 LOW

---

## End-to-End Integration Flow

### Documentation Query Flow

```
User Question → UI Service → Agent Service → Router
                                           ↓
                                    Docs Expert Tool
                                           ↓
                                    Docs Service → LanceDB
                                           ↓
                                    Ollama (LLM)
                                           ↓
                              Cited Answer → UI
```

### Code Scanning Flow

```
Code Input → UI Service → Scanner Service → Bandit/Semgrep
                                         ↓
                                 Unified Findings
                                         ↓
                                   LLM Explainer (Ollama)
                                         ↓
                          Remediation Advice → UI
```

### Web Search Flow

```
Query → UI Service → Agent Service → Router
                                   ↓
                            Web Guide Tool
                                   ↓
                         Web Guide Service
                         ↙            ↘
                    SearXNG        GitHub API
                         ↘            ↙
                          Ranking Engine
                                   ↓
                         Ranked Results → UI
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker Compose logs
cd infrastructure/docker
docker-compose logs

# Restart specific service
docker-compose restart agent-service

# Rebuild specific service
docker-compose build --no-cache docs-service
docker-compose up -d docs-service
```

### Ollama Connection Issues

```bash
# Verify Ollama is running
ollama list

# Test Ollama from container
docker exec -it sourcely-agent curl http://host.docker.internal:11434/api/tags

# Check host.docker.internal resolution (Windows/Mac)
# On Linux, use host.docker.internal:host-gateway in extra_hosts
```

### Documentation Not Found

```bash
# Check if docs are ingested
curl http://localhost:8001/stats

# Re-ingest documentation
curl -X POST http://localhost:8001/ingest/all

# Check vector store exists
docker exec -it sourcely-docs ls -la /app/data/vectordb
```

### Scanner Not Detecting Issues

```bash
# Verify scanners are installed in container
docker exec -it sourcely-scanner bandit --version
docker exec -it sourcely-scanner semgrep --version

# Check scanner service logs
docker-compose logs scanner-service
```

### Web Search Returns Empty

```bash
# Verify SearXNG is running
curl http://localhost:8080

# Check webguide service can reach SearXNG
docker exec -it sourcely-webguide curl http://searxng:8080

# View webguide logs
docker-compose logs webguide-service
```

---

## Performance Tuning

### LanceDB Optimization

```python
# In services/docs_service/app/core/config.py

# Adjust chunk size for better retrieval
max_chunk_tokens: int = 512  # Increase for more context
min_chunk_tokens: int = 50   # Decrease for finer granularity

# Adjust overlap for better context preservation
chunk_overlap_percent: float = 0.125  # Increase to 0.15 for more overlap
```

### Embedding Model Selection

```python
# Faster but less accurate
embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims

# More accurate but slower
embedding_model: str = "sentence-transformers/all-mpnet-base-v2"  # 768 dims
```

### Scanner Timeout

```python
# In services/scanner_service/app/core/config.py

scan_timeout_seconds: int = 60  # Increase for large files
```

---

## Development Workflow

### Run Services Locally (Without Docker)

#### 1. Agent Service

```bash
cd services/agent_services
pip install -e ".[dev]"
uvicorn app.main:app --port 8000 --reload
```

#### 2. Docs Service

```bash
cd services/docs_service
pip install -e ".[dev]"
uvicorn app.main:app --port 8001 --reload
```

#### 3. Scanner Service

```bash
cd services/scanner_service
pip install -e ".[dev]"
pip install bandit semgrep
uvicorn app.main:app --port 8002 --reload
```

#### 4. Web Guide Service

```bash
cd services/webguide_service
pip install -e ".[dev]"
uvicorn app.main:app --port 8003 --reload
```

#### 5. UI Service

```bash
cd services/ui_service
pip install -r requirements.txt
streamlit run app.py
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

# Run evaluation
cd evals
python run_eval.py
```

---

## API Reference Quick Links

- **Agent API**: http://localhost:8000/docs
- **Docs API**: http://localhost:8001/docs
- **Scanner API**: http://localhost:8002/docs
- **Web Guide API**: http://localhost:8003/docs
- **Streamlit UI**: http://localhost:8501

---

## Next Steps

1. **Customize Documentation**: Add your own documentation sources
2. **Tune Ranking**: Adjust weights in `services/webguide_service/app/search/ranking.py`
3. **Add Custom Scanners**: Extend scanner service with additional tools
4. **Deploy to Kubernetes**: See `deploy/` directory (coming soon)
5. **Enable Observability**: Configure LangFuse, Prometheus (coming soon)

---

## Support

For issues:
1. Check service logs: `docker-compose logs <service-name>`
2. Review health endpoints: `curl http://localhost:<port>/health`
3. Verify Ollama models: `ollama list`
4. Check documentation stats: `curl http://localhost:8001/stats`

**Project Version**: 0.1.0  
**Last Updated**: November 8, 2026

# Sourcely: AI Developer Agent

**An agentic AI system that assists developers with documentation search, web research, code security scanning, and safe code execution.**

Built with LangGraph, Ollama (local LLM), and microservices architecture. Weeks 1-3 complete.

---

## 🎯 Core Capabilities

| Tool | Description | Port |
|------|-------------|------|
| **Docs Expert** | RAG-powered documentation search with LanceDB vector store and multi-source ingestion | 8002 |
| **Web Guide** | Intelligent web + GitHub search with SearXNG, ranking, filtering, and LLM summarization | 8003 |
| **Security Scanner** | Vulnerability detection with Bandit + Semgrep, LLM-powered explanations | 8004 |
| **Secure Sandbox** | Isolated Docker-in-Docker Python execution with blockchain audit ledger | 8001 |
| **Agent** | LangGraph orchestration with dynamic tool routing and fallback logic | 8000 |
| **UI** | Streamlit multi-page interface for agent chat, docs Q&A, and scanner | 8501 |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI (8501)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent Service (LangGraph) (8000)               │
│  ┌────────────┬─────────────┬────────────┬──────────────┐  │
│  │ Docs Tool  │  Web Tool   │ Scan Tool  │ Sandbox Tool │  │
│  └─────┬──────┴──────┬──────┴─────┬──────┴───────┬──────┘  │
└────────┼─────────────┼────────────┼──────────────┼─────────┘
         │             │            │              │
    ┌────▼────┐  ┌────▼────┐  ┌───▼────┐  ┌──────▼──────┐
    │  Docs   │  │Webguide │  │Scanner │  │  Sandbox    │
    │ Service │  │ Service │  │Service │  │  Service    │
    │  8002   │  │  8003   │  │  8004  │  │   8001      │
    └─────────┘  └────┬────┘  └────────┘  └──────┬──────┘
                      │                           │
                 ┌────▼────┐               ┌─────▼──────┐
                 │ SearXNG │               │   Ledger   │
                 │  8080   │               │  (SQLite)  │
                 └─────────┘               └────────────┘
```

**Technology Stack:**
- **Agent:** LangGraph + Ollama (qwen3:4b)
- **Vector Store:** LanceDB
- **Web Search:** SearXNG + GitHub API
- **Scanners:** Bandit (AST), Semgrep (SAST)
- **Sandbox:** Docker-in-Docker with security hardening
- **Ledger:** Hash-chained blockchain audit trail
- **UI:** Streamlit
- **Orchestration:** Docker Compose

---

## 🚀 Quickstart

### Prerequisites

- **Docker** and **Docker Compose**
- **Ollama** installed and running locally
- **Python 3.12+** (for local development)
- **Git**

### 1. Install Ollama

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com/download

# Pull the model
ollama pull qwen3:4b
```

### 2. Clone & Configure

```bash
git clone <repository-url>
cd Sourcely

# Create environment file
cp .env.example .env

# Generate SEARXNG_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))" > /tmp/secret.txt
# Copy the output to .env SEARXNG_SECRET field
```

### 3. Start Services

```bash
cd infrastructure/docker
docker-compose up --build -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f agent-service
```

### 4. Ingest Documentation

```bash
# Create sample Kubernetes documentation
curl -X POST http://localhost:8002/ingest/sample -H "Content-Type: application/json"

# Verify ingestion
curl http://localhost:8002/health
```

### 5. Open UI

Navigate to **http://localhost:8501**

Try:
- **Agent Chat:** Ask "What is a Kubernetes Pod?"
- **Docs Q&A:** Search documentation
- **Security Scanner:** Scan code for vulnerabilities

---

## 🧪 Running Tests

### Unit Tests (Per Service)

```bash
# Agent service
cd services/agent_services
pytest tests/ -v

# Docs service
cd services/docs_service
pytest tests/ -v

# Webguide service
cd services/webguide_service
pytest tests/unit/ -v

# Scanner service (includes 22 vulnerable snippets)
cd services/scanner_service
pytest tests/ -v

# Sandbox service (includes adversarial tests)
cd services/sandbox_service
pytest tests/unit/ -v
```

### Integration Tests

```bash
cd services/webguide_service
pytest tests/integration/ -v
```

### RAG Evaluation (52 Q&A Test Cases)

```bash
cd evals
python run_eval.py

# Expected output:
# - Retrieval accuracy
# - Answer quality scores
# - Citation accuracy
# - 52 test cases from golden_dataset.json
```

---

## 📊 Test Coverage

| Service | Unit Tests | Integration Tests | Vulnerable Snippets | Adversarial Tests |
|---------|-----------|-------------------|---------------------|-------------------|
| Agent | ✅ 3 files | - | - | - |
| Docs | ✅ 2 files | - | - | - |
| Webguide | ✅ 5 files | ✅ 4 files | - | - |
| Scanner | ✅ 10 tests | - | ✅ 22 snippets | - |
| Sandbox | ✅ 7 files | ✅ 3 files | - | ✅ 14 scenarios |
| **Evaluation** | - | - | **52 Q&A pairs** | - |

---

## 🔒 Security

### Sandbox Hardening

The sandbox service executes untrusted code in isolated Docker containers with comprehensive security controls:

| Control | Configuration | Purpose |
|---------|---------------|---------|
| User | `nobody:nogroup` (65534:65534) | Non-root execution |
| Filesystem | Read-only + /tmp tmpfs | Prevents persistence |
| Network | Disabled (`network_mode: none`) | Prevents exfiltration |
| Capabilities | All dropped | Removes privileges |
| CPU | 0.5 cores | Prevents monopolization |
| Memory | 128MB | Prevents exhaustion |
| PIDs | 32 max | Prevents fork bombs |
| Timeout | 30 seconds | Prevents infinite loops |

**Audit Trail:** Every execution is recorded in a hash-chained blockchain ledger (SQLite) with tamper-evident properties.

See [docs/security_tests.md](docs/security_tests.md) for detailed adversarial test results.

---

## 📁 Project Structure

```
Sourcely/
├── services/
│   ├── agent_services/      # LangGraph orchestration
│   ├── docs_service/         # RAG documentation search
│   ├── webguide_service/     # Web + GitHub search
│   ├── scanner_service/      # Security vulnerability scanning
│   ├── sandbox_service/      # Isolated code execution
│   └── ui_service/           # Streamlit frontend
├── infrastructure/
│   └── docker/
│       └── docker-compose.yml  # Service orchestration
├── docs/
│   ├── adr/                  # Architecture Decision Records
│   └── security_tests.md     # Adversarial test documentation
├── evals/
│   ├── golden_dataset.json   # 52 Q&A test cases
│   └── run_eval.py           # Evaluation harness
└── scripts/
    └── verify_integration.py # End-to-end integration test
```

---

## 🛠️ Development

### Local Service Development

```bash
# Example: Run docs service locally
cd services/docs_service
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8002

# Run tests with coverage
pytest --cov=app tests/ -v
```

### Adding Documentation Sources

```python
# Edit services/docs_service/app/ingestion/doc_sources.py

def create_custom_docs(framework: str) -> list[Document]:
    """Add your documentation source here."""
    # Implement scraping or API integration
    pass
```

### Linting & Formatting

```bash
cd services/agent_services
ruff check app tests
ruff format app tests
```

---

## 📖 Architecture Decision Records

Key architectural decisions are documented in `docs/adr/`:

1. **[001-monorepo-modular-monolith](docs/adr/001-monorepo-modular-monolith.md)** - Monorepo with microservices
2. **[002-local-llm-ollama](docs/adr/002-local-llm-ollama.md)** - Local LLM via Ollama
3. **[003-langgraph-orchestration](docs/adr/003-langgraph-orchestration.md)** - LangGraph for agent orchestration

---

## 🎯 Roadmap

### ✅ Weeks 1-3 Complete (100%)

- [x] Docs Expert with LanceDB RAG
- [x] Multi-source documentation ingestion
- [x] Web Guide with SearXNG + GitHub search
- [x] Intelligent ranking and LLM summarization
- [x] Security Scanner with Bandit + Semgrep
- [x] LLM-powered vulnerability explanations
- [x] Secure Sandbox with Docker isolation
- [x] Hash-chained blockchain audit ledger
- [x] Streamlit UI with multi-page interface
- [x] 52 Q&A evaluation dataset (260% of target)
- [x] 22 vulnerable code snippet test suite
- [x] 14 adversarial security test scenarios
- [x] GitHub CI/CD with Ruff + Pytest

### 🚧 Week 4+ (Future)

- [ ] Kubernetes deployment (k3s/k8s)
- [ ] Helm charts for all services
- [ ] ArgoCD for GitOps deployment
- [ ] Kafka/Redpanda for event streaming
- [ ] Distributed tracing (Jaeger)
- [ ] Centralized logging (ELK/Loki)
- [ ] Horizontal pod autoscaling
- [ ] Multi-language sandbox support (Node.js, Go, Rust)

---

## 📝 API Documentation

Once services are running, visit:

- **Agent API:** http://localhost:8000/docs
- **Docs API:** http://localhost:8002/docs
- **Webguide API:** http://localhost:8003/docs
- **Scanner API:** http://localhost:8004/docs
- **Sandbox API:** http://localhost:8001/docs (internal only)

---

## 🤝 Contributing

This is an educational project demonstrating:
- LangGraph agent orchestration
- Local LLM integration (Ollama)
- RAG with LanceDB
- Microservices architecture
- Docker security hardening
- Blockchain audit trails

Feel free to explore, learn, and extend!

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

**Team Contributions:**

- **Eya** (Weeks 1, 3): Docs Expert, RAG pipeline, evaluation harness, Security Scanner, UI service
- **Malak** (Weeks 2, 3): Web Guide, SearXNG integration, GitHub search, Secure Sandbox, audit ledger

**Technologies:**

- LangChain/LangGraph for agent orchestration
- Ollama for local LLM inference
- LanceDB for vector storage
- SearXNG for privacy-respecting web search
- Bandit & Semgrep for security scanning
- Docker for containerization and isolation

---

**Status:** ✅ Weeks 1-3 Complete | Ready for Week 4 (Kubernetes)

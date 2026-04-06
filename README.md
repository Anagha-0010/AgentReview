# 🤖 AgentReview

An agentic AI system that automatically reviews GitHub Pull Requests using RAG-powered context retrieval and a multi-agent LangGraph pipeline.

> Built as a portfolio project demonstrating production-grade Agentic AI, RAG, and MLOps practices.

---

## Demo

**How it works:**
1. A PR is opened on GitHub
2. GitHub sends a webhook to the FastAPI backend
3. A LangGraph agent retrieves relevant codebase context via RAG (ChromaDB)
4. An analysis agent reviews the diff for bugs, security issues, performance problems, and style
5. A synthesis agent writes a structured review comment posted back to the PR automatically

---

## Architecture
```
GitHub PR Webhook
       ↓
FastAPI Gateway (async, HMAC signature verification)
       ↓
LangGraph Orchestrator (stateful multi-agent pipeline)
   ├── Retrieval Agent   → ChromaDB semantic search (RAG)
   ├── Analysis Agent    → Bug, security, performance, style detection
   └── Synthesis Agent   → Structured PR comment generation
       ↓
GitHub API (posts review comment)
       ↓
Streamlit Dashboard (metrics, history, manual trigger)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| LLM inference | Groq API (llama-3.3-70b-versatile) |
| Backend API | FastAPI + asyncio |
| Vector store | ChromaDB (persistent) |
| Code chunking | AST-aware (function/class boundaries) |
| Frontend | Streamlit |
| Logging | Loguru |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Key Features

- **AST-aware code chunking** — splits code at function and class boundaries rather than arbitrary token windows, improving retrieval relevance
- **Multi-agent pipeline** — separate agents for retrieval, analysis, and synthesis with full latency tracking per step
- **Persistent vector store** — ChromaDB persists to disk so codebase context survives server restarts
- **Webhook security** — HMAC SHA-256 signature verification on all GitHub webhook payloads
- **Structured analysis** — agent outputs typed JSON (bugs, security, performance, style) before synthesizing the final comment
- **Observability** — per-review metrics tracked including latency breakdown, issue counts by type, and recommendation history
- **Streamlit dashboard** — live metrics, charts, review history, and manual review trigger

---

## Project Structure
```
agentreview/
├── src/
│   ├── agents/
│   │   ├── base.py              # Shared Groq LLM client
│   │   ├── orchestrator.py      # LangGraph state machine
│   │   └── prompts.py           # All prompt templates
│   ├── api/
│   │   └── main.py              # FastAPI app + webhook endpoint
│   ├── core/
│   │   ├── config.py            # Pydantic settings
│   │   ├── logging.py           # Loguru setup
│   │   └── storage.py           # Review history persistence
│   ├── rag/
│   │   ├── chunker.py           # AST-aware code chunker
│   │   ├── embedder.py          # Embedding wrapper
│   │   └── vector_store.py      # ChromaDB interface
│   ├── github/
│   │   ├── client.py            # GitHub API client
│   │   └── parser.py            # PR diff parser
│   └── ui/
│       └── dashboard.py         # Streamlit dashboard
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── railway.toml
├── tests/
├── notebooks/
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- [uv](https://astral.sh/uv) package manager
- [Groq API key](https://console.groq.com) (free)
- GitHub account + Personal Access Token

### Installation
```bash
# Clone the repo
git clone https://github.com/Anagha-0010/AgentReview.git
cd AgentReview

# Install dependencies
uv sync

# Copy environment variables
cp .env.example .env
# Fill in your API keys in .env
```

### Environment Variables
```env
GROQ_API_KEY=your_groq_key
GITHUB_TOKEN=your_github_pat
GITHUB_WEBHOOK_SECRET=your_webhook_secret
LLM_MODEL=llama-3.3-70b-versatile
```

Generate a webhook secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Run locally
```bash
# Start the API server
uvicorn src.api.main:app --reload --port 8000

# Start the dashboard (separate terminal)
streamlit run src/ui/dashboard.py --server.fileWatcherType none
```

### Run with Docker
```bash
docker-compose -f deploy/docker-compose.yml up --build
```

---

## Setting up the GitHub Webhook

1. Go to your repo → **Settings → Webhooks → Add webhook**
2. Set Payload URL to `https://your-domain.com/webhook/github`
3. Content type: `application/json`
4. Secret: your `GITHUB_WEBHOOK_SECRET`
5. Select **Pull requests** events only

To test locally, use [ngrok](https://ngrok.com) to expose port 8000:
```bash
ngrok http 8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/health` | Status + vector store chunk count |
| POST | `/webhook/github` | GitHub webhook receiver |
| POST | `/reindex` | Re-index codebase into vector store |

---

## Dashboard

The Streamlit dashboard at `http://localhost:8501` shows:

- **Overview metrics** — total reviews, issues found, avg latency, recommendations
- **Issues by type chart** — bugs vs security vs performance vs style across all reviews
- **Latency per review chart** — agent pipeline performance over time
- **Agent step breakdown** — retrieve / analyze / synthesize latency for the latest review
- **Manual review trigger** — paste any git diff and run a review instantly
- **Review history** — full history with per-review metrics and expandable comments

---

## How the Agent Pipeline Works
```
1. RETRIEVE
   - LLM generates 3-5 semantic search queries from the PR diff
   - Queries run against ChromaDB vector store
   - Top 8 unique code chunks retrieved as context

2. ANALYZE  
   - LLM receives diff + retrieved context
   - Returns structured JSON: { bugs, security, performance, style, summary }
   
3. SYNTHESIZE
   - LLM receives analysis JSON
   - Writes markdown PR review comment
   - Includes APPROVE / REQUEST_CHANGES / COMMENT recommendation
```

---

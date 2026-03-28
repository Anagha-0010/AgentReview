import hashlib
import hmac
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from loguru import logger
from src.core.config import settings
from src.core.logging import setup_logging
from src.rag.chunker import ASTCodeChunker
from src.rag.vector_store import CodeVectorStore
from src.agents.orchestrator import ReviewOrchestrator
from src.github.client import GitHubClient

setup_logging()

vector_store = None
orchestrator = None
github_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store, orchestrator, github_client
    logger.info("Starting AgentReview...")
    vector_store = CodeVectorStore()
    orchestrator = ReviewOrchestrator(vector_store=vector_store)
    github_client = GitHubClient()
    logger.info("AgentReview ready!")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="AgentReview", version="0.1.0", lifespan=lifespan)

def verify_github_signature(payload: bytes, signature: str) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

async def run_review(repo_full_name: str, pr_number: int):
    try:
        logger.info(f"Running review for PR #{pr_number}")
        pr_data = github_client.get_pr_data(repo_full_name, pr_number)

        if not pr_data.diff:
            logger.warning("No diff found, skipping review")
            return

        result = orchestrator.review(pr_data.diff)
        github_client.post_review_comment(
            repo_full_name, pr_number, result["review_comment"]
        )
        logger.info(f"Review posted for PR #{pr_number}")
    except Exception as e:
        logger.error(f"Review failed for PR #{pr_number}: {e}")

@app.get("/")
async def root():
    return {"status": "AgentReview is running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "vector_store_chunks": vector_store.count() if vector_store else 0
    }

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if settings.github_webhook_secret and not verify_github_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return {"status": "ignored", "event": event}

    payload = json.loads(payload_bytes)
    action = payload.get("action", "")

    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "action": action}

    repo_full_name = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]

    background_tasks.add_task(run_review, repo_full_name, pr_number)
    return {"status": "review started", "pr": pr_number}
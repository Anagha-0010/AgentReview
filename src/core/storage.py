import json
from pathlib import Path
from datetime import datetime
from loguru import logger

STORAGE_FILE = Path("logs/reviews.json")

def save_review(pr_number: int, repo: str, diff: str, comment: str, queries: list):
    STORAGE_FILE.parent.mkdir(exist_ok=True)
    reviews = load_reviews()
    reviews.append({
        "id": len(reviews) + 1,
        "timestamp": datetime.now().isoformat(),
        "pr_number": pr_number,
        "repo": repo,
        "diff_length": len(diff),
        "comment": comment,
        "queries": queries,
        "chunk_count": len(queries)
    })
    STORAGE_FILE.write_text(json.dumps(reviews, indent=2))
    logger.info(f"Saved review #{pr_number} to storage")

def load_reviews() -> list:
    if not STORAGE_FILE.exists():
        return []
    try:
        return json.loads(STORAGE_FILE.read_text())
    except Exception:
        return []
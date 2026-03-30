import json
from pathlib import Path
from datetime import datetime
from loguru import logger

STORAGE_FILE = Path(__file__).resolve().parent.parent.parent / "logs" / "reviews.json"

def save_review(
    pr_number: int,
    repo: str,
    diff: str,
    comment: str,
    queries: list,
    analysis: dict,
    latency_ms: float
):
    STORAGE_FILE.parent.mkdir(exist_ok=True)
    reviews = load_reviews()

    bugs = len(analysis.get("bugs", []))
    security = len(analysis.get("security", []))
    performance = len(analysis.get("performance", []))
    style = len(analysis.get("style", []))
    total_issues = bugs + security + performance + style

    reviews.append({
        "id": len(reviews) + 1,
        "timestamp": datetime.now().isoformat(),
        "pr_number": pr_number,
        "repo": repo,
        "diff_length": len(diff),
        "comment": comment,
        "queries": queries,
        "context_chunks_used": len(queries),
        "latency_ms": round(latency_ms),
        "issues": {
            "bugs": bugs,
            "security": security,
            "performance": performance,
            "style": style,
            "total": total_issues
        },
        "recommendation": _extract_recommendation(comment)
    })

    STORAGE_FILE.write_text(json.dumps(reviews, indent=2))
    logger.info(f"Saved review #{pr_number} — {total_issues} issues found in {round(latency_ms)}ms")

def _extract_recommendation(comment: str) -> str:
    for rec in ["REQUEST_CHANGES", "APPROVE", "COMMENT"]:
        if rec in comment.upper():
            return rec
    return "COMMENT"

def load_reviews() -> list:
    if not STORAGE_FILE.exists():
        return []
    try:
        return json.loads(STORAGE_FILE.read_text())
    except Exception:
        return []
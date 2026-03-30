import streamlit as st
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.storage import load_reviews

st.set_page_config(
    page_title="AgentReview Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AgentReview Dashboard")
st.caption("AI-powered GitHub PR review system")

# ── Sidebar ──────────────────────────────────────────────
st.sidebar.header("System Status")

try:
    response = httpx.get("http://localhost:8000/health", timeout=2)
    health = response.json()
    st.sidebar.success("✅ API is running")
    st.sidebar.metric("Indexed chunks", health.get("vector_store_chunks", 0))
except Exception:
    st.sidebar.error("❌ API is not running")
    st.sidebar.caption("Start the server with: uvicorn src.api.main:app --reload --port 8000")

st.sidebar.divider()
if st.sidebar.button("🔄 Refresh"):
    st.rerun()

# ── Metrics row ───────────────────────────────────────────
reviews = load_reviews()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reviews", len(reviews))
col2.metric("Repos Covered", len(set(r["repo"] for r in reviews)) if reviews else 0)
col3.metric("Avg Diff Size", f"{int(sum(r['diff_length'] for r in reviews) / len(reviews))} chars" if reviews else "N/A")
col4.metric("Avg Queries/Review", f"{sum(r['chunk_count'] for r in reviews) / len(reviews):.1f}" if reviews else "N/A")

st.divider()

# ── Manual review trigger ─────────────────────────────────
st.subheader("🧪 Manual Review")
st.caption("Test the agent by pasting a code diff directly")

sample_diff = """--- a/src/auth.py
+++ b/src/auth.py
@@ -10,6 +10,12 @@
+def login(username, password):
+    query = f"SELECT * FROM users WHERE username='{username}'"
+    result = db.execute(query)
+    if result:
+        return generate_token(result[0])
+    return None"""

diff_input = st.text_area("Paste a git diff here", value=sample_diff, height=200)

if st.button("▶️ Run Review", type="primary"):
    if diff_input.strip():
        with st.spinner("Agent is reviewing..."):
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                from src.rag.chunker import ASTCodeChunker
                from src.rag.vector_store import CodeVectorStore
                from src.agents.orchestrator import ReviewOrchestrator

                @st.cache_resource
                def get_orchestrator():
                    store = CodeVectorStore()
                    chunker = ASTCodeChunker()
                    chunks = chunker.chunk_directory("src")
                    store.add_chunks(chunks)
                    return ReviewOrchestrator(vector_store=store)

                orchestrator = get_orchestrator()
                result = orchestrator.review(diff_input)

                st.success("✅ Review complete!")
                st.markdown("### Review Comment")
                st.markdown(result["review_comment"])

                with st.expander("🔍 Agent internals"):
                    st.write("**Search queries used:**")
                    for q in result.get("search_queries", []):
                        st.write(f"- {q}")
                    st.write("**Raw analysis:**")
                    st.json(result.get("analysis", {}))

            except Exception as e:
                st.error(f"Review failed: {e}")
    else:
        st.warning("Please paste a diff first")

st.divider()

# ── Review history ────────────────────────────────────────
st.subheader("📋 Review History")

if not reviews:
    st.info("No reviews yet — open a PR on GitHub or use the manual trigger above")
else:
    for review in reversed(reviews):
        with st.expander(
            f"PR #{review['pr_number']} · {review['repo']} · {review['timestamp'][:16].replace('T', ' ')}"
        ):
            col1, col2 = st.columns(2)
            col1.metric("Diff size", f"{review['diff_length']} chars")
            col2.metric("Search queries", review['chunk_count'])

            st.markdown("**Review comment:**")
            st.markdown(review["comment"])

            if review.get("queries"):
                st.write("**Queries used:**")
                for q in review["queries"]:
                    st.write(f"- {q}")
import streamlit as st
import httpx
import sys
import json
from pathlib import Path
from datetime import datetime

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
    st.sidebar.success("✅ API running")
    st.sidebar.metric("Indexed chunks", health.get("vector_store_chunks", 0))
except Exception:
    st.sidebar.error("❌ API offline")
    st.sidebar.caption("Run: uvicorn src.api.main:app --reload --port 8000")

if st.sidebar.button("🔄 Refresh"):
    st.rerun()

reviews = load_reviews()

# ── Top metrics ───────────────────────────────────────────
st.subheader("📊 Overview")
col1, col2, col3, col4, col5 = st.columns(5)
total = len(reviews)
total_issues = sum(r.get("issues", {}).get("total", 0) for r in reviews)
avg_latency = sum(r.get("latency_ms", 0) for r in reviews) / total if total else 0
request_changes = sum(1 for r in reviews if r.get("recommendation") == "REQUEST_CHANGES")
approved = sum(1 for r in reviews if r.get("recommendation") == "APPROVE")

col1.metric("Total Reviews", total)
col2.metric("Issues Found", total_issues)
col3.metric("Avg Latency", f"{round(avg_latency)}ms")
col4.metric("Request Changes", request_changes)
col5.metric("Approved", approved)

st.divider()

# ── Charts ────────────────────────────────────────────────
if reviews:
    st.subheader("📈 Metrics")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Issues by type (all reviews)**")
        all_bugs = sum(r.get("issues", {}).get("bugs", 0) for r in reviews)
        all_security = sum(r.get("issues", {}).get("security", 0) for r in reviews)
        all_perf = sum(r.get("issues", {}).get("performance", 0) for r in reviews)
        all_style = sum(r.get("issues", {}).get("style", 0) for r in reviews)

        import pandas as pd
        issue_data = pd.DataFrame({
            "Type": ["Bugs", "Security", "Performance", "Style"],
            "Count": [all_bugs, all_security, all_perf, all_style]
        })
        st.bar_chart(issue_data.set_index("Type"))

    with chart_col2:
        st.markdown("**Latency per review (ms)**")
        latency_data = pd.DataFrame({
            "PR": [f"PR #{r['pr_number']}" for r in reviews],
            "Latency (ms)": [r.get("latency_ms", 0) for r in reviews]
        })
        st.bar_chart(latency_data.set_index("PR"))

    st.divider()

    # Agent step breakdown for latest review
    if reviews:
        latest = reviews[-1]
        st.subheader("⚡ Latest Review — Agent Step Breakdown")
        s1, s2, s3, s4 = st.columns(4)
        latency = latest.get("latency", {})
        s1.metric("Total", f"{latest.get('latency_ms', 0)}ms")
        s2.metric("Retrieve", f"{latency.get('retrieve_ms', 0)}ms")
        s3.metric("Analyze", f"{latency.get('analyze_ms', 0)}ms")
        s4.metric("Synthesize", f"{latency.get('synthesize_ms', 0)}ms")

    st.divider()

# ── Manual review ─────────────────────────────────────────
st.subheader("🧪 Manual Review")
sample_diff = """--- a/src/auth.py
+++ b/src/auth.py
@@ -10,6 +10,12 @@
+def login(username, password):
+    query = f\"SELECT * FROM users WHERE username='{username}'\"
+    result = db.execute(query)
+    if result:
+        return generate_token(result[0])
+    return None"""

diff_input = st.text_area("Paste a git diff", value=sample_diff, height=180)

if st.button("▶️ Run Review", type="primary"):
    if diff_input.strip():
        with st.spinner("Agent is reviewing..."):
            try:
                from src.rag.vector_store import CodeVectorStore
                from src.rag.chunker import ASTCodeChunker
                from src.agents.orchestrator import ReviewOrchestrator

                @st.cache_resource
                def get_orchestrator():
                    store = CodeVectorStore()
                    if store.count() == 0:
                        chunker = ASTCodeChunker()
                        chunks = chunker.chunk_directory("src")
                        store.add_chunks(chunks)
                    return ReviewOrchestrator(vector_store=store)

                orc = get_orchestrator()
                result = orc.review(diff_input)

                st.success("✅ Review complete!")

                m1, m2, m3 = st.columns(3)
                issues = result.get("analysis", {})
                m1.metric("Total issues", sum([
                    len(issues.get("bugs", [])),
                    len(issues.get("security", [])),
                    len(issues.get("performance", [])),
                    len(issues.get("style", []))
                ]))
                m2.metric("Total latency", f"{result.get('latency', {}).get('total_ms', 0)}ms")
                m3.metric("Context chunks", len(result.get("search_queries", [])))

                st.markdown("### Review Comment")
                st.markdown(result["review_comment"])

                with st.expander("🔍 Agent internals"):
                    st.write("**Search queries:**")
                    for q in result.get("search_queries", []):
                        st.write(f"- {q}")
                    st.write("**Raw analysis:**")
                    st.json(result.get("analysis", {}))
                    st.write("**Latency breakdown:**")
                    st.json(result.get("latency", {}))

            except Exception as e:
                st.error(f"Review failed: {e}")
                import traceback
                st.code(traceback.format_exc())

st.divider()

# ── Review history ────────────────────────────────────────
st.subheader("📋 Review History")
if not reviews:
    st.info("No reviews yet — open a PR or use the manual trigger above")
else:
    for review in reversed(reviews):
        issues = review.get("issues", {})
        rec = review.get("recommendation", "COMMENT")
        rec_color = "🔴" if rec == "REQUEST_CHANGES" else "🟢" if rec == "APPROVE" else "🟡"

        with st.expander(
            f"{rec_color} PR #{review['pr_number']} · {review['repo']} · "
            f"{review['timestamp'][:16].replace('T', ' ')} · "
            f"{issues.get('total', 0)} issues · {review.get('latency_ms', 0)}ms"
        ):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Bugs", issues.get("bugs", 0))
            c2.metric("Security", issues.get("security", 0))
            c3.metric("Performance", issues.get("performance", 0))
            c4.metric("Style", issues.get("style", 0))
            c5.metric("Latency", f"{review.get('latency_ms', 0)}ms")

            st.markdown("**Review:**")
            st.markdown(review["comment"])

            if review.get("queries"):
                with st.expander("Search queries used"):
                    for q in review["queries"]:
                        st.write(f"- {q}")
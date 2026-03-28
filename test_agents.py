import sys, traceback
#trying the output
print("Step 1: Setting up vector store...")
try:
    from src.rag.chunker import ASTCodeChunker
    from src.rag.vector_store import CodeVectorStore
    chunker = ASTCodeChunker()
    chunks = chunker.chunk_directory("src")
    store = CodeVectorStore()
    store.add_chunks(chunks)
    print(f"  ✓ Vector store ready with {store.count()} chunks")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 2: Loading orchestrator...")
try:
    from src.agents.orchestrator import ReviewOrchestrator
    orchestrator = ReviewOrchestrator(vector_store=store)
    print("  ✓ Orchestrator ready")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: Running a review...")
SAMPLE_DIFF = """
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,6 +10,12 @@
+def login(username, password):
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    result = db.execute(query)
+    if result:
+        return generate_token(result[0])
+    return None
"""

try:
    result = orchestrator.review(SAMPLE_DIFF)
    print("  ✓ Review complete!\n")
    print("=" * 60)
    print(result["review_comment"])
    print("=" * 60)
except Exception as e:
    print(f"  ✗ Review failed: {e}")
    traceback.print_exc()
    sys.exit(1)

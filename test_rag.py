from src.rag.chunker import ASTCodeChunker
from src.rag.vector_store import CodeVectorStore

#tring a pr 3
# Chunk this project's own source code
chunker = ASTCodeChunker()
chunks = chunker.chunk_directory("src")
print(f"Found {len(chunks)} chunks")

# Store in ChromaDB
store = CodeVectorStore()
store.add_chunks(chunks)
print(f"Stored {store.count()} chunks in vector store")

# Search
query = "how does code get chunked into pieces"
results = store.search(query, n_results=3)
print(f"\nTop 3 results for: '{query}'")
for i, r in enumerate(results):
    print(f"\n--- Result {i+1} ---")
    print(f"File: {r['metadata']['filepath']}")
    print(f"Name: {r['metadata']['name']}")
    print(f"Distance: {r['distance']:.4f}")
    print(f"Preview: {r['content'][:150]}...")

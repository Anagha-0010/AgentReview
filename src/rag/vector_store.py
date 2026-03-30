import chromadb
from pathlib import Path
from loguru import logger
from src.rag.chunker import CodeChunk
from src.rag.embedder import CodeEmbedder

CHROMA_PATH = Path(".chroma")

class CodeVectorStore:
    def __init__(self, collection_name: str = "codebase"):
        CHROMA_PATH.mkdir(exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.embedder = CodeEmbedder()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Vector store ready — {self.collection.count()} chunks loaded from disk")

    def add_chunks(self, chunks: list[CodeChunk]):
        if not chunks:
            return

        ids = [f"{c.filepath}::{c.name}::{c.start_line}" for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [{
            "filepath": c.filepath,
            "chunk_type": c.chunk_type,
            "name": c.name,
            "start_line": c.start_line,
            "end_line": c.end_line
        } for c in chunks]

        embeddings = self.embedder.embed(documents)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        logger.info(f"Added {len(chunks)} chunks to vector store")

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        if self.collection.count() == 0:
            logger.warning("Vector store is empty")
            return []

        query_embedding = self.embedder.embed_single(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count())
        )

        hits = []
        for i, doc in enumerate(results["documents"][0]):
            hits.append({
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        return hits

    def count(self) -> int:
        return self.collection.count()

    def clear(self):
        self.client.delete_collection("codebase")
        self.collection = self.client.get_or_create_collection(
            name="codebase",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Vector store cleared")
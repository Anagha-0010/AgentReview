import ast
from dataclasses import dataclass
from pathlib import Path
from loguru import logger

@dataclass
class CodeChunk:
    content: str
    filepath: str
    chunk_type: str      # "function", "class", "module"
    name: str
    start_line: int
    end_line: int

class ASTCodeChunker:
    def __init__(self, max_chunk_size: int = 1500):
        self.max_chunk_size = max_chunk_size

    def chunk_file(self, filepath: str) -> list[CodeChunk]:
        path = Path(filepath)
        if path.suffix != ".py":
            return self._fallback_chunk(filepath)

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            lines = source.splitlines()
            chunks = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
                    start = node.lineno - 1
                    end = node.end_lineno
                    content = "\n".join(lines[start:end])

                    if len(content) > self.max_chunk_size:
                        content = content[:self.max_chunk_size]

                    chunks.append(CodeChunk(
                        content=content,
                        filepath=filepath,
                        chunk_type=chunk_type,
                        name=node.name,
                        start_line=node.lineno,
                        end_line=node.end_lineno
                    ))

            if not chunks:
                return self._fallback_chunk(filepath)

            logger.debug(f"Chunked {filepath} into {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.warning(f"AST parsing failed for {filepath}: {e}")
            return self._fallback_chunk(filepath)

    def _fallback_chunk(self, filepath: str) -> list[CodeChunk]:
        try:
            content = Path(filepath).read_text(encoding="utf-8")
            chunks = []
            for i in range(0, len(content), self.max_chunk_size):
                chunk = content[i:i + self.max_chunk_size]
                chunks.append(CodeChunk(
                    content=chunk,
                    filepath=filepath,
                    chunk_type="module",
                    name=f"chunk_{i}",
                    start_line=0,
                    end_line=0
                ))
            return chunks
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return []

    def chunk_directory(self, directory: str) -> list[CodeChunk]:
        all_chunks = []
        for path in Path(directory).rglob("*.py"):
            if ".venv" not in str(path) and "__pycache__" not in str(path):
                all_chunks.extend(self.chunk_file(str(path)))
        logger.info(f"Total chunks from {directory}: {len(all_chunks)}")
        return all_chunks
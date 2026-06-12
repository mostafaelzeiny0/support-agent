"""Document ingestion pipeline: load, chunk, embed, and store in ChromaDB."""

import os
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer


class DocumentChunker:
    """Split documents into overlapping chunks."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """
        Split a document into overlapping chunks.

        Args:
            text: Document text
            doc_id: Document identifier

        Returns:
            List of chunk dicts with id, content, source
        """
        chunks = []
        step = self.chunk_size - self.overlap

        for i in range(0, len(text), step):
            chunk_text = text[i:i + self.chunk_size]
            if len(chunk_text.strip()) > 0:
                chunks.append({
                    "id": f"{doc_id}_chunk_{len(chunks)}",
                    "content": chunk_text,
                    "source": doc_id,
                })

        return chunks


class DocumentIngester:
    """Load, chunk, embed, and store documents in ChromaDB."""

    def __init__(
        self,
        policies_dir: Path,
        chroma_dir: Path,
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        overlap: int = 50,
    ):
        self.policies_dir = Path(policies_dir)
        self.chroma_dir = Path(chroma_dir)
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB client
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(str(self.chroma_dir))
        self.collection = None

    def load_policies(self) -> Dict[str, str]:
        """Load all policy .txt files from policies directory."""
        policies = {}
        for policy_file in self.policies_dir.glob("*.txt"):
            with open(policy_file, "r", encoding="utf-8") as f:
                policies[policy_file.stem] = f.read()
        return policies

    def ingest(self) -> int:
        """
        Ingest all policy documents into ChromaDB.

        Returns:
            Total number of chunks ingested
        """
        # Load policy documents
        policies = self.load_policies()
        if not policies:
            raise ValueError(f"No policy files found in {self.policies_dir}")

        # Create chunker
        chunker = DocumentChunker(self.chunk_size, self.overlap)

        # Chunk and prepare documents
        all_chunks = []
        for doc_id, text in policies.items():
            chunks = chunker.chunk_document(text, doc_id)
            all_chunks.extend(chunks)

        # Create collection
        self.collection = self.client.get_or_create_collection(
            name="policies",
            metadata={"hnsw:space": "cosine"}
        )

        # Embed and store in ChromaDB
        for chunk in all_chunks:
            embedding = self.embedding_model.encode(chunk["content"]).tolist()
            self.collection.add(
                ids=[chunk["id"]],
                embeddings=[embedding],
                metadatas=[{"source": chunk["source"]}],
                documents=[chunk["content"]],
            )

        return len(all_chunks)


def ingest_policies(
    policies_dir: Path,
    chroma_dir: Path,
) -> int:
    """
    Convenience function to ingest all policies into ChromaDB.

    Args:
        policies_dir: Directory containing policy .txt files
        chroma_dir: Directory to persist ChromaDB

    Returns:
        Number of chunks ingested
    """
    ingester = DocumentIngester(policies_dir, chroma_dir)
    return ingester.ingest()

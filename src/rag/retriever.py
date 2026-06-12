"""Naive RAG retriever: simple similarity search over indexed documents."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer


class NaiveRetriever:
    """Simple similarity-based retriever without reranking or advanced features."""

    def __init__(
        self,
        chroma_dir: Path,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.chroma_dir = Path(chroma_dir)
        self.embedding_model = SentenceTransformer(embedding_model)

        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(str(self.chroma_dir))
        try:
            self.collection = self.client.get_collection("policies")
        except ValueError:
            self.collection = None

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top-k documents similar to the query.

        Args:
            query: Search query
            k: Number of documents to retrieve

        Returns:
            List of retrieved documents with content and metadata
        """
        if self.collection is None:
            return []

        # Embed the query
        query_embedding = self.embedding_model.encode(query).tolist()

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )

        # Format results
        documents = []
        if results and results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                doc_dict = {
                    "id": results["ids"][0][i] if results["ids"] else f"doc_{i}",
                    "content": doc,
                    "source": results["metadatas"][0][i].get("source", "unknown") if results["metadatas"] else "unknown",
                    "relevance_score": 1.0 - (results["distances"][0][i] / 2.0) if results["distances"] else 0.5,
                }
                documents.append(doc_dict)

        return documents


_retriever = None


def get_retriever(chroma_dir: Optional[Path] = None) -> NaiveRetriever:
    """Get or create the naive retriever singleton."""
    global _retriever
    if _retriever is None:
        if chroma_dir is None:
            chroma_dir = Path(__file__).parent.parent.parent / "data" / "chroma_db"
        _retriever = NaiveRetriever(chroma_dir)
    return _retriever

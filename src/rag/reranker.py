"""Reranking module using cross-encoder to improve retrieval quality."""

from typing import List, Dict, Any
from sentence_transformers import CrossEncoder


class DocumentReranker:
    """Rerank documents using a cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize reranker with cross-encoder.

        Args:
            model_name: HuggingFace cross-encoder model name
        """
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on query-document relevance.

        Cross-encoder scores query-document pairs directly (0.0-1.0).
        This is more accurate than embedding-based methods but slower.

        Args:
            query: Search query
            documents: List of documents with 'content' field
            top_n: Number of documents to return after reranking

        Returns:
            Reranked documents sorted by relevance score
        """
        if not documents:
            return []

        # Prepare pairs for cross-encoder: (query, document)
        pairs = [
            [query, doc["content"]] for doc in documents
        ]

        # Get cross-encoder scores
        scores = self.model.predict(pairs)

        # Add scores to documents and sort
        scored_docs = []
        for i, doc in enumerate(documents):
            doc_copy = doc.copy()
            doc_copy["reranker_score"] = float(scores[i])
            scored_docs.append(doc_copy)

        # Sort by reranker score (descending)
        ranked = sorted(scored_docs, key=lambda x: x["reranker_score"], reverse=True)

        return ranked[:top_n]


_reranker = None


def get_reranker() -> DocumentReranker:
    """Get or create the reranker singleton."""
    global _reranker
    if _reranker is None:
        _reranker = DocumentReranker()
    return _reranker

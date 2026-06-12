"""Hybrid retrieval combining semantic search + BM25 keyword search."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi


class HybridRetriever:
    """Hybrid retriever combining semantic + keyword search with rank fusion."""

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

        # Build BM25 index from all documents
        self._build_bm25_index()

    def _build_bm25_index(self):
        """Build BM25 index from all documents in ChromaDB."""
        if self.collection is None:
            self.bm25 = None
            self.doc_texts = {}
            return

        # Get all documents
        results = self.collection.get()
        self.doc_texts = {}
        documents = []

        if results and results["documents"]:
            for doc_id, doc_text in zip(results["ids"], results["documents"]):
                self.doc_texts[doc_id] = doc_text
                # Tokenize for BM25
                tokens = doc_text.lower().split()
                documents.append(tokens)

        # Build BM25 corpus
        if documents:
            self.bm25 = BM25Okapi(documents)
        else:
            self.bm25 = None

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve documents using hybrid search (semantic + keyword).

        Process:
        1. Semantic search via ChromaDB cosine similarity
        2. Keyword search via BM25
        3. Rank fusion (reciprocal rank fusion)
        4. Return top-k merged results

        Args:
            query: Search query
            k: Number of documents to retrieve

        Returns:
            List of retrieved documents with content and metadata
        """
        if self.collection is None or self.bm25 is None:
            return []

        # Get all documents for context
        all_results = self.collection.get()
        all_doc_ids = all_results["ids"] if all_results and all_results["ids"] else []

        # 1. Semantic search
        query_embedding = self.embedding_model.encode(query).tolist()
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k * 2, len(all_doc_ids)),  # Get more for fusion
        )

        semantic_scores = {}
        if semantic_results and semantic_results["documents"] and len(semantic_results["documents"]) > 0:
            for i, doc_id in enumerate(semantic_results["ids"][0]):
                # Convert distance to similarity (cosine)
                distance = semantic_results["distances"][0][i] if semantic_results["distances"] else 1.0
                similarity = 1.0 - (distance / 2.0)
                semantic_scores[doc_id] = similarity

        # 2. Keyword search (BM25)
        query_tokens = query.lower().split()
        bm25_scores_raw = self.bm25.get_scores(query_tokens)

        bm25_scores = {}
        if all_doc_ids:
            for doc_id, score in zip(all_doc_ids, bm25_scores_raw):
                if score > 0:
                    bm25_scores[doc_id] = score

        # 3. Rank fusion (Reciprocal Rank Fusion)
        fused_scores = {}
        all_doc_ids_set = set(all_doc_ids)

        for doc_id in all_doc_ids_set:
            rrf_score = 0.0

            # RRF formula: 1 / (k + rank)
            if doc_id in semantic_scores:
                ranked_ids = sorted(semantic_scores.keys(), key=semantic_scores.get, reverse=True)
                rank = ranked_ids.index(doc_id) + 1 if doc_id in ranked_ids else len(ranked_ids) + 1
                rrf_score += 1.0 / (60 + rank)

            if doc_id in bm25_scores:
                ranked_ids = sorted(bm25_scores.keys(), key=bm25_scores.get, reverse=True)
                rank = ranked_ids.index(doc_id) + 1 if doc_id in ranked_ids else len(ranked_ids) + 1
                rrf_score += 1.0 / (60 + rank)

            if rrf_score > 0:
                fused_scores[doc_id] = rrf_score

        # 4. Get top-k and format results
        top_doc_ids = sorted(fused_scores.keys(), key=fused_scores.get, reverse=True)[:k]

        documents = []
        for doc_id in top_doc_ids:
            doc_content = self.doc_texts.get(doc_id, "")

            # Get metadata
            metadata = None
            all_results_dict = self.collection.get(ids=[doc_id])
            if all_results_dict and all_results_dict["metadatas"] and len(all_results_dict["metadatas"]) > 0:
                metadata = all_results_dict["metadatas"][0]

            doc_dict = {
                "id": doc_id,
                "content": doc_content,
                "source": metadata.get("source", "unknown") if metadata else "unknown",
                "relevance_score": fused_scores[doc_id],
            }
            documents.append(doc_dict)

        return documents


_retriever = None


def get_hybrid_retriever(chroma_dir: Optional[Path] = None) -> HybridRetriever:
    """Get or create the hybrid retriever singleton."""
    global _retriever
    if _retriever is None:
        if chroma_dir is None:
            chroma_dir = Path(__file__).parent.parent.parent / "data" / "chroma_db"
        _retriever = HybridRetriever(chroma_dir)
    return _retriever

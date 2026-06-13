"""Document ingestion pipeline: load, chunk, embed, and store in ChromaDB."""

import os
import re
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer


class DocumentChunker:
    """Split documents into chunks respecting sentence boundaries."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _extract_section_title(self, text: str) -> str:
        """Extract the first heading as section title."""
        match = re.search(r'^#+\s+(.+)$', text, re.MULTILINE)
        return match.group(1) if match else "General"

    def chunk_document(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """
        Split a document into chunks respecting sentence boundaries.
        Uses recursive splitting: paragraph -> sentence -> character level.

        Args:
            text: Document text
            doc_id: Document identifier (e.g., "policy", "faq")

        Returns:
            List of chunk dicts with id, content, source, and metadata
        """
        # Try paragraph-level split first
        separators = ["\n\n", "\n", ". ", " "]
        chunks = []

        def recursive_split(text: str, separators: List[str]) -> List[str]:
            """Recursively split text by separators."""
            if not text.strip():
                return []

            good_splits = []
            separator = separators[-1]

            for _s in separators:
                if _s == "":
                    separator = _s
                    break
                if _s in text:
                    separator = _s
                    break

            if separator:
                splits = text.split(separator)
            else:
                splits = list(text)

            good_splits = [s for s in splits if len(s.strip()) > 0]

            if len("".join(good_splits)) < self.chunk_size:
                return good_splits

            final_chunks = []
            good_split = ""
            for s in good_splits:
                if len(good_split) + len(s) < self.chunk_size:
                    good_split += s + separator
                else:
                    if good_split:
                        final_chunks.append(good_split)
                    good_split = s + separator

            if good_split:
                final_chunks.append(good_split)

            return final_chunks

        # Split text hierarchically
        split_chunks = recursive_split(text, separators)

        # Extract document type
        doc_type = self._get_document_type(doc_id)
        section_title = self._extract_section_title(text)

        # Create chunks with metadata
        for idx, chunk_text in enumerate(split_chunks):
            if len(chunk_text.strip()) > 0:
                chunks.append({
                    "id": f"{doc_id}_chunk_{idx}",
                    "content": chunk_text.strip(),
                    "source": doc_id,
                    "metadata": {
                        "document_type": doc_type,
                        "section_title": section_title,
                        "chunk_index": idx,
                    }
                })

        return chunks

    def _get_document_type(self, doc_id: str) -> str:
        """Infer document type from doc_id."""
        if "policy" in doc_id.lower() or "return" in doc_id.lower():
            return "policy"
        elif "faq" in doc_id.lower():
            return "faq"
        elif "shipping" in doc_id.lower():
            return "shipping"
        else:
            return "general"


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
            metadata = chunk.get("metadata", {})
            metadata["source"] = chunk["source"]

            self.collection.add(
                ids=[chunk["id"]],
                embeddings=[embedding],
                metadatas=[metadata],
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

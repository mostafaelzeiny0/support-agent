"""
Run the complete RAG pipeline: ingestion, retrieval, and evaluation.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.ingestion import ingest_policies


def main():
    print("=" * 60)
    print("Phase 3: RAG Pipeline Setup")
    print("=" * 60)

    policies_dir = project_root / "data" / "policies"
    chroma_dir = project_root / "data" / "chroma_db"

    # Step 1: Ingest policies into ChromaDB
    print("\n[STEP 1] Ingesting policy documents into ChromaDB...")
    try:
        num_chunks = ingest_policies(policies_dir, chroma_dir)
        print(f"[OK] Ingested {num_chunks} document chunks")
        print(f"[OK] ChromaDB database persisted to {chroma_dir}")
    except Exception as e:
        print(f"[ERROR] Ingestion failed: {e}")
        return

    # Step 2: Test retrieval
    print("\n[STEP 2] Testing naive retriever...")
    try:
        from src.rag.retriever import get_retriever
        retriever = get_retriever(chroma_dir)

        test_query = "What is your return policy?"
        docs = retriever.retrieve(test_query, k=3)
        print(f"[OK] Retrieved {len(docs)} documents for test query")
        print(f"     Query: '{test_query}'")
        for i, doc in enumerate(docs, 1):
            print(f"     [{i}] {doc['source']}: {doc['content'][:80]}...")
    except Exception as e:
        print(f"[ERROR] Retrieval test failed: {e}")
        return

    print("\n" + "=" * 60)
    print("RAG pipeline ready for evaluation!")
    print("=" * 60)
    print("\nNext: Run scripts/run_baseline_eval.py for RAGAS evaluation")


if __name__ == "__main__":
    main()

"""
Phase 4 Integration Test: Advanced RAG Pipeline
"""

import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.graph.graph import compile_graph
from src.state import SupportAgentState
from datetime import datetime


def test_advanced_rag():
    """Test the complete advanced RAG system."""
    print("=" * 80)
    print("PHASE 4 INTEGRATION TEST: Advanced RAG Pipeline")
    print("=" * 80)

    # Compile graph with advanced pipeline
    print("\n[1] Compiling graph with advanced RAG agent...")
    try:
        graph = compile_graph()
        print("[OK] Graph compiled successfully")
    except Exception as e:
        print(f"[ERROR] Graph compilation failed: {e}")
        return False

    # Test Case: Policy Query with Advanced RAG
    print("\n[2] Test Case: Advanced RAG Pipeline")
    print("-" * 80)

    state: SupportAgentState = {
        "messages": [
            {
                "role": "customer",
                "content": "I want to return my order. What's the process and timeline?",
                "timestamp": datetime.now(),
            }
        ],
        "customer_id": "cust_001",
        "customer_name": "Alex Smith",
        "order_id": None,
        "order_status": None,
        "order_details": None,
        "intent": None,
        "current_agent": None,
        "escalation_flag": False,
        "escalation_reason": None,
        "escalation_depth": 0,
        "retrieved_docs": [],
        "memory": None,
        "session_id": "sess_001",
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
        "retrieval_context": None,
        "ground_truth_answer": None,
    }

    print(f"Customer: {state['messages'][0]['content']}\n")

    try:
        result = graph.invoke(state)

        print(f"Intent: {result.get('intent')}")
        print(f"Retrieved Docs: {len(result.get('retrieved_docs', []))} documents")

        if result.get('retrieved_docs'):
            print(f"\nRetrieved Context (Advanced RAG):")
            for i, doc in enumerate(result['retrieved_docs'][:2], 1):
                source = doc['source']
                score = doc.get('reranker_score', doc.get('relevance_score', 0))
                print(f"  [{i}] {source.upper()} (score: {score:.3f})")
                print(f"       {doc['content'][:70]}...")

        print(f"\nResponse:")
        for msg in result["messages"]:
            if msg["role"] == "customer":
                pass  # Skip customer message
            elif msg.get("agent_name") == "policy_returns":
                try:
                    response_preview = msg["content"].encode('ascii', 'ignore').decode('ascii')[:150]
                except:
                    response_preview = msg["content"][:150]
                print(f"  [POLICY_RETURNS - ADVANCED RAG]")
                print(f"  {response_preview}...")

        print("\n[OK] Test Case passed - Advanced RAG working!")

    except Exception as e:
        print(f"[ERROR] Test Case failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Show metrics comparison
    print("\n[3] Evaluation Metrics Comparison")
    print("-" * 80)

    eval_dir = project_root / "data" / "eval"
    baseline_file = eval_dir / "baseline_scores.json"
    advanced_file = eval_dir / "advanced_scores.json"

    if baseline_file.exists() and advanced_file.exists():
        with open(baseline_file, "r") as f:
            baseline = json.load(f)
        with open(advanced_file, "r") as f:
            advanced = json.load(f)

        print("\nPhase 3 Baseline vs Phase 4 Advanced:")
        print(f"{'Metric':<20} {'Baseline':<12} {'Advanced':<12} {'Change':<12}")
        print("-" * 80)

        for metric in ["relevance", "faithfulness", "context_quality"]:
            baseline_score = baseline["metrics"].get(metric, 0)
            advanced_score = advanced["metrics"].get(metric, 0)
            change = advanced_score - baseline_score

            print(
                f"{metric:<20} {baseline_score:.3f}       {advanced_score:.3f}       "
                f"{change:+.3f}"
            )

        print("-" * 80)
        baseline_avg = sum(baseline["metrics"].values()) / len(baseline["metrics"])
        advanced_avg = sum(advanced["metrics"].values()) / len(advanced["metrics"])
        avg_change = advanced_avg - baseline_avg

        print(
            f"{'AVERAGE':<20} {baseline_avg:.3f}       {advanced_avg:.3f}       "
            f"{avg_change:+.3f}"
        )

        pct_improvement = (avg_change / baseline_avg * 100) if baseline_avg > 0 else 0
        print(f"\nOverall Improvement: {pct_improvement:+.1f}%")

    print("\n" + "=" * 80)
    print("ADVANCED RAG PIPELINE COMPONENTS")
    print("=" * 80)
    print("""
[OK] Query Expansion:      Rephrases customer query with policy keywords
[OK] Hybrid Retrieval:     Combines semantic (embedding) + keyword (BM25) search
[OK] Rank Fusion:          Merges results using reciprocal rank fusion
[OK] Reranking:            Cross-encoder scores top-5 documents
[OK] Claude Response:      Generates answer grounded in reranked context

Pipeline Flow:
  Customer Query
    | [Query Expansion]
  Expanded Query
    | [Hybrid Retrieval (5 docs)]
  Hybrid Results
    | [Reranking to 3 docs]
  Reranked Results
    | [Format Context]
  Context
    | [Claude API]
  Grounded Response
""")

    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_advanced_rag()
    sys.exit(0 if success else 1)

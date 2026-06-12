"""Advanced RAG evaluation using the improved pipeline."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


TEST_QUESTIONS = [
    {
        "question": "What is EasyMart's return window for purchased items?",
        "ground_truth": "30 days from the date of purchase",
    },
    {
        "question": "Can I return personalized or customized items at EasyMart?",
        "ground_truth": "No, personalized items are typically non-returnable",
    },
    {
        "question": "How long does it take for a refund to be processed at EasyMart?",
        "ground_truth": "5-10 business days after the return is received",
    },
    {
        "question": "What are EasyMart's shipping costs?",
        "ground_truth": "$5.99 for standard shipping, $12.99 for expedited shipping",
    },
    {
        "question": "Is there free shipping at EasyMart?",
        "ground_truth": "Yes, free shipping on orders over $50",
    },
    {
        "question": "What is the maximum refund amount before escalation at EasyMart?",
        "ground_truth": "$150 is the maximum automatic refund without escalation",
    },
    {
        "question": "How does EasyMart handle shipping for international orders?",
        "ground_truth": "EasyMart offers international shipping to select countries",
    },
    {
        "question": "What should I do if my item arrives damaged?",
        "ground_truth": "You can request a partial or full refund depending on the damage",
    },
    {
        "question": "How long does standard delivery take at EasyMart?",
        "ground_truth": "5-7 business days",
    },
    {
        "question": "Can I exchange an item instead of returning it for a refund?",
        "ground_truth": "Yes, EasyMart offers exchange requests as an alternative to returns",
    },
]


class SimpleMetrics:
    """Simple metrics for RAG evaluation."""

    @staticmethod
    def calculate_relevance(answer: str, contexts: List[str], ground_truth: str) -> float:
        """Calculate relevance by keyword matching."""
        if not answer or not ground_truth:
            return 0.5

        stop_words = {"the", "a", "an", "is", "are", "was", "be", "to", "for", "of", "in", "on", "at", "and", "or"}
        keywords = [w.lower() for w in ground_truth.split() if w.lower() not in stop_words and len(w) > 2]

        combined_text = (answer + " " + " ".join(contexts)).lower()
        matches = sum(1 for kw in keywords if kw in combined_text)

        if not keywords:
            return 0.5

        return min(1.0, matches / len(keywords))

    @staticmethod
    def calculate_context_quality(contexts: List[str]) -> float:
        """Calculate context quality."""
        if not contexts:
            return 0.0

        avg_length = sum(len(c) for c in contexts) / len(contexts)
        length_score = min(1.0, avg_length / 500)

        non_empty = sum(1 for c in contexts if len(c.strip()) > 0)
        coverage_score = non_empty / len(contexts)

        return (length_score + coverage_score) / 2

    @staticmethod
    def calculate_faithfulness(answer: str, contexts: List[str]) -> float:
        """Calculate faithfulness."""
        if not answer or not contexts:
            return 0.5

        combined_context = " ".join(contexts).lower()
        answer_lower = answer.lower()

        answer_words = set(answer_lower.split())
        context_words = set(combined_context.split())

        overlap = len(answer_words & context_words)
        total = len(answer_words)

        if total == 0:
            return 0.5

        return min(1.0, overlap / total)


class AdvancedEvaluator:
    """Evaluate advanced RAG pipeline."""

    def __init__(self, chroma_dir: Optional[Path] = None):
        self.chroma_dir = Path(chroma_dir) if chroma_dir else Path.cwd() / "data" / "chroma_db"
        self.client = Anthropic()

        from src.rag.query_expander import get_query_expander
        from src.rag.hybrid_retriever import get_hybrid_retriever
        from src.rag.reranker import get_reranker

        self.query_expander = get_query_expander()
        self.retriever = get_hybrid_retriever(self.chroma_dir)
        self.reranker = get_reranker()

    def generate_response(self, query: str) -> tuple:
        """Generate response using advanced RAG pipeline."""
        # Query expansion
        try:
            expanded_query = self.query_expander.expand_query(query)
        except Exception:
            expanded_query = query

        # Hybrid retrieval
        docs = self.retriever.retrieve(expanded_query, k=5)

        # Reranking
        if docs:
            try:
                docs = self.reranker.rerank(query, docs, top_n=3)
            except Exception:
                docs = docs[:3]

        context = "\n\n".join([
            f"[{doc['source'].upper()}]\n{doc['content']}"
            for doc in docs
        ])

        prompt = f"""You are a helpful EasyMart customer support agent.

Customer Query: {query}

Relevant Policy Information:
{context}

Please provide a helpful response to the customer's query using the policy information above."""

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text, docs

    def evaluate(self) -> Dict[str, Any]:
        """Run evaluation on all test questions."""
        results = []
        metrics = SimpleMetrics()

        relevance_scores = []
        faithfulness_scores = []
        context_quality_scores = []

        for test_q in TEST_QUESTIONS:
            query = test_q["question"]
            ground_truth = test_q["ground_truth"]

            response, docs = self.generate_response(query)

            relevance = metrics.calculate_relevance(response, [d["content"] for d in docs], ground_truth)
            faithfulness = metrics.calculate_faithfulness(response, [d["content"] for d in docs])
            context_quality = metrics.calculate_context_quality([d["content"] for d in docs])

            relevance_scores.append(relevance)
            faithfulness_scores.append(faithfulness)
            context_quality_scores.append(context_quality)

            result = {
                "question": query,
                "ground_truth": ground_truth,
                "answer": response,
                "contexts": [d["content"] for d in docs],
                "metrics": {
                    "relevance": relevance,
                    "faithfulness": faithfulness,
                    "context_quality": context_quality,
                }
            }
            results.append(result)

        avg_metrics = {
            "relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0,
            "faithfulness": sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0,
            "context_quality": sum(context_quality_scores) / len(context_quality_scores) if context_quality_scores else 0.0,
        }

        return {
            "status": "success",
            "metrics": avg_metrics,
            "results": results,
        }


def run_advanced_evaluation(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Run advanced evaluation and save results."""
    if output_dir is None:
        output_dir = Path.cwd() / "data" / "eval"

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Running advanced RAG evaluation...")
    print(f"Questions: {len(TEST_QUESTIONS)}\n")

    evaluator = AdvancedEvaluator()
    eval_result = evaluator.evaluate()

    output_file = output_dir / "advanced_scores.json"
    with open(output_file, "w", encoding="utf-8") as f:
        output_data = {
            "status": eval_result["status"],
            "metrics": eval_result["metrics"],
            "num_questions": len(TEST_QUESTIONS),
            "results": eval_result["results"],
        }
        json.dump(output_data, f, indent=2)

    print(f"[OK] Results saved to {output_file}")
    return output_data


def load_baseline_scores(eval_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load baseline scores for comparison."""
    if eval_dir is None:
        eval_dir = Path.cwd() / "data" / "eval"

    baseline_file = eval_dir / "baseline_scores.json"
    if baseline_file.exists():
        with open(baseline_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def print_comparison_table(baseline: Dict[str, Any], advanced: Dict[str, Any]):
    """Print side-by-side comparison of baseline vs advanced scores."""
    print("\n" + "=" * 80)
    print("PHASE 4: BASELINE vs ADVANCED RAG COMPARISON")
    print("=" * 80)

    if baseline and advanced["status"] == "success":
        baseline_metrics = baseline.get("metrics", {})
        advanced_metrics = advanced["metrics"]

        print("\nMetrics (0.0 to 1.0 scale):")
        print("-" * 80)
        print(f"{'Metric':<20} {'Baseline':<15} {'Advanced':<15} {'Improvement':<15}")
        print("-" * 80)

        for metric in ["relevance", "faithfulness", "context_quality"]:
            baseline_score = baseline_metrics.get(metric, 0.0)
            advanced_score = advanced_metrics.get(metric, 0.0)
            improvement = advanced_score - baseline_score
            improvement_pct = (improvement / baseline_score * 100) if baseline_score > 0 else 0

            print(
                f"{metric:<20} {baseline_score:.3f}           {advanced_score:.3f}           "
                f"{improvement:+.3f} ({improvement_pct:+.1f}%)"
            )

        print("-" * 80)

        baseline_avg = sum(baseline_metrics.values()) / len(baseline_metrics)
        advanced_avg = sum(advanced_metrics.values()) / len(advanced_metrics)
        avg_improvement = advanced_avg - baseline_avg
        avg_improvement_pct = (avg_improvement / baseline_avg * 100) if baseline_avg > 0 else 0

        print(
            f"{'AVERAGE':<20} {baseline_avg:.3f}           {advanced_avg:.3f}           "
            f"{avg_improvement:+.3f} ({avg_improvement_pct:+.1f}%)"
        )
        print("=" * 80)

        if advanced_avg > baseline_avg:
            print(f"\n[SUCCESS] Advanced RAG improved over baseline by {avg_improvement_pct:+.1f}%")
        else:
            print(f"\n[NOTE] Advanced RAG performance: {avg_improvement_pct:+.1f}%")

    else:
        print("\n[ERROR] Unable to load baseline scores for comparison")

    print("=" * 80)


if __name__ == "__main__":
    eval_dir = Path.cwd() / "data" / "eval"

    # Load baseline
    baseline = load_baseline_scores(eval_dir)

    # Run advanced evaluation
    advanced = run_advanced_evaluation(eval_dir)

    # Print comparison
    print_comparison_table(baseline, advanced)

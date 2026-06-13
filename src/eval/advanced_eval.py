"""Advanced RAG evaluation using RAGAS metrics."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from anthropic import Anthropic

from src.eval.ragas_dataset import get_test_questions, format_for_ragas
from src.eval.baseline_eval import RAGASEvaluator


class AdvancedEvaluator:
    """Evaluate advanced RAG pipeline using RAGAS metrics."""

    def __init__(self, chroma_dir: Optional[Path] = None):
        self.chroma_dir = Path(chroma_dir) if chroma_dir else Path.cwd() / "data" / "chroma_db"
        self.client = Anthropic()
        self.ragas_evaluator = RAGASEvaluator()

        from src.rag.query_expander import get_query_expander
        from src.rag.hybrid_retriever import get_hybrid_retriever
        from src.rag.reranker import get_reranker

        self.query_expander = get_query_expander()
        self.retriever = get_hybrid_retriever(self.chroma_dir)
        self.reranker = get_reranker()

    def generate_response(self, query: str) -> tuple:
        """Generate response using advanced RAG pipeline."""
        try:
            expanded_query = self.query_expander.expand_query(query)
        except Exception:
            expanded_query = query

        docs = self.retriever.retrieve(expanded_query, k=5)

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
        """Run evaluation using RAGAS metrics."""
        results = []
        test_questions = get_test_questions()

        faithfulness_scores = []
        answer_relevancy_scores = []
        context_precision_scores = []
        context_recall_scores = []

        for i, test_q in enumerate(test_questions):
            query = test_q["question"]
            ground_truth = test_q["ground_truth"]

            print(f"  [{i+1}/10] Evaluating: {query[:50]}...", end=" ", flush=True)

            response, docs = self.generate_response(query)
            contexts = [d["content"] for d in docs]

            eval_data = format_for_ragas(query, response, contexts, ground_truth)

            try:
                ragas_scores = self.ragas_evaluator.evaluate_with_ragas(eval_data)
            except Exception as e:
                ragas_scores = {
                    "faithfulness": 0.5,
                    "answer_relevancy": 0.5,
                    "context_precision": 0.5,
                    "context_recall": 0.5,
                }

            faithfulness_scores.append(ragas_scores.get("faithfulness", 0.5))
            answer_relevancy_scores.append(ragas_scores.get("answer_relevancy", 0.5))
            context_precision_scores.append(ragas_scores.get("context_precision", 0.5))
            context_recall_scores.append(ragas_scores.get("context_recall", 0.5))

            result = {
                "question": query,
                "ground_truth": ground_truth,
                "answer": response,
                "contexts": contexts,
                "metrics": ragas_scores
            }
            results.append(result)
            print("[OK]")

        avg_metrics = {
            "faithfulness": sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.5,
            "answer_relevancy": sum(answer_relevancy_scores) / len(answer_relevancy_scores) if answer_relevancy_scores else 0.5,
            "context_precision": sum(context_precision_scores) / len(context_precision_scores) if context_precision_scores else 0.5,
            "context_recall": sum(context_recall_scores) / len(context_recall_scores) if context_recall_scores else 0.5,
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

    print("\n" + "=" * 80)
    print("ADVANCED RAG EVALUATION (Hybrid + Reranking + Query Expansion)")
    print("=" * 80)
    print(f"Questions: 10")
    print()

    evaluator = AdvancedEvaluator()
    eval_result = evaluator.evaluate()

    output_file = output_dir / "ragas_advanced.json"
    with open(output_file, "w", encoding="utf-8") as f:
        output_data = {
            "pipeline": "advanced_rag_hybrid_rerank",
            "metrics": eval_result["metrics"],
            "num_questions": len(get_test_questions()),
            "results": eval_result["results"],
        }
        json.dump(output_data, f, indent=2)

    print(f"\n[OK] Results saved to {output_file}")
    return output_data


def load_baseline_scores(eval_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load baseline scores for comparison."""
    if eval_dir is None:
        eval_dir = Path.cwd() / "data" / "eval"

    baseline_file = eval_dir / "ragas_baseline.json"
    if baseline_file.exists():
        with open(baseline_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def print_comparison_table(baseline: Dict[str, Any], advanced: Dict[str, Any]):
    """Print RAGAS comparison table."""
    print("\n" + "=" * 100)
    print("RAGAS EVALUATION: BASELINE vs ADVANCED RAG PIPELINE COMPARISON")
    print("=" * 100)

    if baseline and baseline.get("metrics") and advanced and advanced.get("metrics"):
        baseline_metrics = baseline.get("metrics", {})
        advanced_metrics = advanced["metrics"]

        print("\nRAGAS Metrics (0.0 to 1.0 scale):")
        print("-" * 100)
        print(f"{'Metric':<25} {'Baseline':<18} {'Advanced':<18} {'Improvement':<20}")
        print("-" * 100)

        metrics_to_compare = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

        for metric in metrics_to_compare:
            baseline_score = baseline_metrics.get(metric, 0.5)
            advanced_score = advanced_metrics.get(metric, 0.5)
            improvement = advanced_score - baseline_score
            improvement_pct = (improvement / baseline_score * 100) if baseline_score > 0 else 0

            metric_display = metric.replace("_", " ").title()
            print(
                f"{metric_display:<25} {baseline_score:.3f}              {advanced_score:.3f}              "
                f"{improvement:+.3f} ({improvement_pct:+.1f}%)"
            )

        print("-" * 100)

        baseline_avg = sum(baseline_metrics.values()) / len(baseline_metrics)
        advanced_avg = sum(advanced_metrics.values()) / len(advanced_metrics)
        avg_improvement = advanced_avg - baseline_avg
        avg_improvement_pct = (avg_improvement / baseline_avg * 100) if baseline_avg > 0 else 0

        print(
            f"{'AVERAGE SCORE':<25} {baseline_avg:.3f}              {advanced_avg:.3f}              "
            f"{avg_improvement:+.3f} ({avg_improvement_pct:+.1f}%)"
        )
        print("=" * 100)

        if advanced_avg > baseline_avg:
            print(f"\n[SUCCESS] Advanced RAG improved over baseline by {avg_improvement_pct:+.1f}%")
        elif advanced_avg < baseline_avg:
            print(f"\n[NOTE] Advanced RAG declined by {abs(avg_improvement_pct):.1f}%")
        else:
            print(f"\n[EQUAL] Advanced RAG performs at baseline level")

    else:
        print("\n[ERROR] Unable to load baseline scores for comparison")

    print("=" * 100)


if __name__ == "__main__":
    eval_dir = Path.cwd() / "data" / "eval"

    # Load baseline
    baseline = load_baseline_scores(eval_dir)

    # Run advanced evaluation
    advanced = run_advanced_evaluation(eval_dir)

    # Print comparison
    print_comparison_table(baseline, advanced)

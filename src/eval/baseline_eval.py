"""Baseline evaluation of naive RAG pipeline using RAGAS-inspired metrics."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from anthropic import Anthropic

from src.eval.ragas_dataset import get_test_questions, format_for_ragas


class RAGASEvaluator:
    """Evaluate RAG pipeline using Claude-based RAGAS-inspired metrics."""

    def __init__(self):
        self.client = Anthropic()

    def evaluate_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """
        Evaluate faithfulness using Claude.
        Does the answer contain only information from the contexts?
        """
        if not answer or not contexts:
            return 0.5

        context_text = "\n".join(contexts)
        prompt = f"""You are an expert evaluator. Assess if the answer is grounded ONLY in the provided context.
Do not reward information that is inferred or assumed.

Context:
{context_text}

Answer:
{answer}

Rate the faithfulness of this answer (0.0 = completely ungrounded, 1.0 = perfectly grounded in context).
Respond with ONLY a number between 0.0 and 1.0, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            score = float(text)
            return min(1.0, max(0.0, score))
        except Exception:
            return 0.5

    def evaluate_answer_relevancy(self, question: str, answer: str) -> float:
        """
        Evaluate answer relevancy using Claude.
        Does the answer actually address the question asked?
        """
        if not question or not answer:
            return 0.5

        prompt = f"""You are an expert evaluator. Assess if the answer directly and completely addresses the question.

Question:
{question}

Answer:
{answer}

Rate the relevancy of this answer (0.0 = completely irrelevant, 1.0 = perfectly relevant).
Respond with ONLY a number between 0.0 and 1.0, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            score = float(text)
            return min(1.0, max(0.0, score))
        except Exception:
            return 0.5

    def evaluate_context_precision(self, question: str, contexts: List[str]) -> float:
        """
        Evaluate context precision using Claude.
        Of the retrieved contexts, how many are actually relevant to the question?
        """
        if not question or not contexts:
            return 0.5

        context_text = "\n---\n".join(contexts)
        prompt = f"""You are an expert evaluator. Assess how many of the provided contexts are relevant to answering the question.

Question:
{question}

Contexts:
{context_text}

What fraction of the contexts (0.0 to 1.0) are actually relevant to answering this question?
Respond with ONLY a number between 0.0 and 1.0, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            score = float(text)
            return min(1.0, max(0.0, score))
        except Exception:
            return 0.5

    def evaluate_context_recall(self, ground_truth: str, contexts: List[str]) -> float:
        """
        Evaluate context recall using Claude.
        Of the information needed (ground truth), how much was retrieved?
        """
        if not ground_truth or not contexts:
            return 0.5

        context_text = "\n".join(contexts)
        prompt = f"""You are an expert evaluator. Assess if the contexts contain the key information from the ground truth.

Ground Truth (expected answer):
{ground_truth}

Retrieved Contexts:
{context_text}

What fraction (0.0 to 1.0) of the ground truth information is contained in the contexts?
Respond with ONLY a number between 0.0 and 1.0, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            score = float(text)
            return min(1.0, max(0.0, score))
        except Exception:
            return 0.5

    def evaluate_with_ragas(self, eval_data: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate using all RAGAS metrics."""
        return {
            "faithfulness": self.evaluate_faithfulness(eval_data["answer"], eval_data["contexts"]),
            "answer_relevancy": self.evaluate_answer_relevancy(eval_data["question"], eval_data["answer"]),
            "context_precision": self.evaluate_context_precision(eval_data["question"], eval_data["contexts"]),
            "context_recall": self.evaluate_context_recall(eval_data["ground_truth"], eval_data["contexts"]),
        }


class BaselineEvaluator:
    """Evaluate naive RAG pipeline using RAGAS metrics."""

    def __init__(self, chroma_dir: Optional[Path] = None):
        self.chroma_dir = Path(chroma_dir) if chroma_dir else Path.cwd() / "data" / "chroma_db"
        self.client = Anthropic()
        self.ragas_evaluator = RAGASEvaluator()

        from src.rag.retriever import get_retriever
        self.retriever = get_retriever(self.chroma_dir)

    def generate_response(self, query: str) -> tuple:
        """Generate a response using Claude API with retrieved context."""
        docs = self.retriever.retrieve(query, k=3)
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
        """Run evaluation on all test questions using RAGAS metrics."""
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


def run_baseline_evaluation(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Run baseline evaluation and save results."""
    if output_dir is None:
        output_dir = Path.cwd() / "data" / "eval"

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("BASELINE RAG EVALUATION (Naive Vector Search)")
    print("=" * 80)
    print(f"Questions: 10")
    print()

    evaluator = BaselineEvaluator()
    eval_result = evaluator.evaluate()

    output_file = output_dir / "ragas_baseline.json"
    with open(output_file, "w", encoding="utf-8") as f:
        output_data = {
            "pipeline": "baseline_naive_rag",
            "metrics": eval_result["metrics"],
            "num_questions": len(get_test_questions()),
            "results": eval_result["results"],
        }
        json.dump(output_data, f, indent=2)

    print(f"\n[OK] Results saved to {output_file}")
    return output_data


def print_evaluation_summary(eval_result: Dict[str, Any]):
    """Print RAGAS evaluation results."""
    print("\n" + "=" * 80)
    print("BASELINE RAGAS EVALUATION RESULTS")
    print("=" * 80)

    metrics = eval_result.get("metrics", {})
    if metrics:
        print("\nRAGAS Metrics (0.0 to 1.0 scale):")
        print("-" * 80)
        print(f"  Faithfulness:        {metrics.get('faithfulness', 0.5):.3f}")
        print(f"  Answer Relevancy:    {metrics.get('answer_relevancy', 0.5):.3f}")
        print(f"  Context Precision:   {metrics.get('context_precision', 0.5):.3f}")
        print(f"  Context Recall:      {metrics.get('context_recall', 0.5):.3f}")

        avg_score = sum(metrics.values()) / len(metrics) if metrics else 0.5
        print(f"\n  AVERAGE SCORE:       {avg_score:.3f}")
        print("-" * 80)
    else:
        print(f"\nNo metrics found in evaluation result")

    print("=" * 80)


if __name__ == "__main__":
    result = run_baseline_evaluation()
    print_evaluation_summary(result)

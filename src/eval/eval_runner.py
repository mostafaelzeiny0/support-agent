"""Run all test conversations through the system and collect metrics."""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from src.graph.graph import compile_graph
from src.state import SupportAgentState
from src.eval.llm_judge import judge_response


class EvaluationRunner:
    """Run test conversations and collect evaluation metrics."""

    def __init__(self):
        self.graph = compile_graph()
        self.results = []

    def run_conversation(self, test_conv: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test conversation."""
        customer_message = test_conv.get("customer_message", "")
        expected_intent = test_conv.get("expected_intent", "")
        category = test_conv.get("category", "unknown")

        # Create initial state
        state = {
            "messages": [
                {
                    "role": "customer",
                    "content": customer_message,
                    "timestamp": datetime.now(),
                }
            ],
            "customer_id": "cust_eval",
            "customer_name": "Eval Customer",
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
            "session_id": "sess_eval",
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
            "retrieval_context": None,
            "ground_truth_answer": None,
        }

        # Run through graph with timing
        start_time = time.time()
        try:
            result_state = self.graph.invoke(state)
            latency = time.time() - start_time

            # Extract metrics
            actual_intent = result_state.get("intent", "unknown")
            escalated = result_state.get("escalation_flag", False)

            # Get agent response
            agent_response = ""
            for msg in reversed(result_state.get("messages", [])):
                if msg.get("role") == "agent":
                    agent_response = msg.get("content", "")
                    break

            # Get context
            context_str = ""
            if result_state.get("retrieved_docs"):
                context_str = " ".join(
                    [doc.get("content", "")[:100] for doc in result_state["retrieved_docs"][:3]]
                )

            # Score with LLM judge
            scores = judge_response(customer_message, agent_response, context_str)

            return {
                "input": customer_message,
                "expected_intent": expected_intent,
                "actual_intent": actual_intent,
                "category": category,
                "intent_match": expected_intent == actual_intent,
                "escalated": escalated,
                "response": agent_response[:200],
                "latency": latency,
                "context_count": len(result_state.get("retrieved_docs", [])),
                "scores": scores,
                "success": True,
            }

        except Exception as e:
            return {
                "input": customer_message,
                "expected_intent": expected_intent,
                "actual_intent": "error",
                "category": category,
                "intent_match": False,
                "escalated": False,
                "response": f"Error: {str(e)}",
                "latency": time.time() - start_time,
                "context_count": 0,
                "scores": {"policy_compliance": 0, "helpfulness": 0, "groundedness": 0},
                "success": False,
            }

    def run_all(self, test_conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run all test conversations."""
        self.results = []

        for i, conv in enumerate(test_conversations):
            print(f"[{i+1}/{len(test_conversations)}] Running conversation: {conv.get('customer_message', '')[:50]}...", end=" ", flush=True)

            result = self.run_conversation(conv)
            self.results.append(result)

            status = "[OK]" if result["success"] else "[ERROR]"
            print(f"{status} Intent: {result['actual_intent']} Latency: {result['latency']:.2f}s")

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Calculate summary metrics."""
        if not self.results:
            return {}

        successful = [r for r in self.results if r["success"]]
        if not successful:
            return {}

        # Intent accuracy
        intent_matches = sum(1 for r in successful if r["intent_match"])
        intent_accuracy = intent_matches / len(successful)

        # Resolution rate (not escalated)
        resolved = sum(1 for r in successful if not r["escalated"])
        resolution_rate = resolved / len(successful)

        # Average latency
        avg_latency = sum(r["latency"] for r in successful) / len(successful)

        # LLM judge scores
        policy_scores = [r["scores"]["policy_compliance"] for r in successful]
        helpfulness_scores = [r["scores"]["helpfulness"] for r in successful]
        groundedness_scores = [r["scores"]["groundedness"] for r in successful]

        avg_policy = sum(policy_scores) / len(policy_scores) if policy_scores else 0
        avg_helpfulness = sum(helpfulness_scores) / len(helpfulness_scores) if helpfulness_scores else 0
        avg_groundedness = sum(groundedness_scores) / len(groundedness_scores) if groundedness_scores else 0

        # Category breakdown
        by_category = {}
        for r in successful:
            cat = r.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = {"total": 0, "resolved": 0, "intent_match": 0}
            by_category[cat]["total"] += 1
            if not r["escalated"]:
                by_category[cat]["resolved"] += 1
            if r["intent_match"]:
                by_category[cat]["intent_match"] += 1

        return {
            "total_conversations": len(successful),
            "intent_accuracy": intent_accuracy,
            "resolution_rate": resolution_rate,
            "avg_latency": avg_latency,
            "policy_compliance": avg_policy,
            "helpfulness": avg_helpfulness,
            "groundedness": avg_groundedness,
            "by_category": by_category,
        }


def save_eval_results(results: List[Dict[str, Any]], summary: Dict[str, Any], output_path: Path):
    """Save evaluation results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved results to {output_path}")

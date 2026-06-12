"""Run full evaluation suite and generate metrics report."""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eval.eval_runner import EvaluationRunner, save_eval_results
from src.eval.generate_test_conversations import generate_test_conversations, save_test_conversations


def load_test_conversations() -> list:
    """Load test conversations from file, or generate if missing."""
    conv_path = project_root / "data" / "eval" / "test_conversations.json"

    if conv_path.exists():
        with open(conv_path, "r", encoding="utf-8") as f:
            conversations = json.load(f)
        print(f"[OK] Loaded {len(conversations)} test conversations from {conv_path}")
        return conversations
    else:
        print("[*] Test conversations not found, generating...")
        conversations = generate_test_conversations()
        if conversations:
            save_test_conversations(conversations, conv_path)
            return conversations
        else:
            print("[ERROR] Failed to generate test conversations")
            return []


def print_summary_table(summary: dict, results: list):
    """Print a clean summary table of metrics."""
    print("\n" + "=" * 80)
    print("EASYMART SUPPORT AGENT - EVALUATION REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Overall metrics
    print("OVERALL METRICS")
    print("-" * 80)
    print(f"  Total Conversations:      {summary.get('total_conversations', 0)}")
    print(f"  Intent Accuracy:          {summary.get('intent_accuracy', 0):.1%}")
    print(f"  Resolution Rate:          {summary.get('resolution_rate', 0):.1%}")
    print(f"  Average Latency:          {summary.get('avg_latency', 0):.2f}s")
    print()

    # LLM Judge Scores
    print("RESPONSE QUALITY SCORES (LLM Judge, 0-1 scale)")
    print("-" * 80)
    print(f"  Policy Compliance:        {summary.get('policy_compliance', 0):.3f}")
    print(f"  Helpfulness:              {summary.get('helpfulness', 0):.3f}")
    print(f"  Groundedness:             {summary.get('groundedness', 0):.3f}")
    print()

    # Category breakdown
    print("PERFORMANCE BY CATEGORY")
    print("-" * 80)
    by_category = summary.get("by_category", {})

    if by_category:
        # Header
        print(f"  {'Category':<15} {'Total':<8} {'Resolved':<10} {'Intent Acc':<12} {'Res Rate':<10}")
        print("  " + "-" * 76)

        # Data rows
        for cat in sorted(by_category.keys()):
            metrics = by_category[cat]
            total = metrics.get("total", 0)
            resolved = metrics.get("resolved", 0)
            intent_match = metrics.get("intent_match", 0)

            cat_name = cat.replace("_", " ").title()
            intent_acc = f"{intent_match/total:.1%}" if total > 0 else "0%"
            res_rate = f"{resolved/total:.1%}" if total > 0 else "0%"

            print(f"  {cat_name:<15} {total:<8} {resolved:<10} {intent_acc:<12} {res_rate:<10}")

    print()

    # Sample results
    print("SAMPLE CONVERSATIONS (first 5)")
    print("-" * 80)
    if results:
        # Header
        print(f"  {'#':<3} {'Category':<15} {'Intent':<15} {'Match':<7} {'Escalated':<12} {'Latency':<10}")
        print("  " + "-" * 76)

        # Data rows
        for i, result in enumerate(results[:5]):
            cat = result.get("category", "unknown").replace("_", " ").title()
            intent = result.get("actual_intent", "N/A")[:14]
            match = "Y" if result.get("intent_match") else "N"
            esc = "Yes" if result.get("escalated") else "No"
            lat = f"{result.get('latency', 0):.2f}s"

            print(f"  {i+1:<3} {cat:<15} {intent:<15} {match:<7} {esc:<12} {lat:<10}")

    print()
    print("=" * 80)
    print(f"Report complete. Results saved to data/eval/full_eval_results.json")
    print("=" * 80)


def main():
    print("\n" + "=" * 80)
    print("EASYMART EVALUATION SUITE")
    print("=" * 80)

    # Load test conversations
    print("\n[1/3] Loading test conversations...")
    conversations = load_test_conversations()

    if not conversations:
        print("[ERROR] No test conversations available")
        return

    # Run evaluation
    print(f"\n[2/3] Running evaluation on {len(conversations)} conversations...")
    runner = EvaluationRunner()
    runner.run_all(conversations)

    # Get summary
    print("\n[3/3] Calculating metrics...")
    summary = runner.get_summary()

    # Save results
    output_path = project_root / "data" / "eval" / "full_eval_results.json"
    save_eval_results(runner.results, summary, output_path)

    # Print summary
    print_summary_table(summary, runner.results)

    # Print category breakdown in detail
    print("\nDETAILED CATEGORY BREAKDOWN:")
    print("-" * 80)
    by_category = summary.get("by_category", {})
    for cat in sorted(by_category.keys()):
        metrics = by_category[cat]
        print(f"\n{cat.upper().replace('_', ' ')}:")
        print(f"  Total conversations: {metrics.get('total', 0)}")
        print(f"  Resolved (no escalation): {metrics.get('resolved', 0)}")
        print(f"  Intent accuracy: {metrics.get('intent_match', 0)} / {metrics.get('total', 1)}")

    print("\n[OK] Evaluation complete!")
    print(f"[OK] Results saved to: {output_path}")
    print("\nTo view interactive dashboard, run:")
    print("  streamlit run src/eval/dashboard.py")


if __name__ == "__main__":
    main()

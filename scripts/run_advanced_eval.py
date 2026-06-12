"""
Run advanced RAG evaluation with comparison to baseline.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eval.advanced_eval import run_advanced_evaluation, load_baseline_scores, print_comparison_table


def main():
    eval_dir = project_root / "data" / "eval"

    # Load baseline
    print("Loading baseline scores...")
    baseline = load_baseline_scores(eval_dir)

    if not baseline:
        print("[ERROR] Baseline scores not found. Run phase 3 evaluation first.")
        return

    # Run advanced evaluation
    print("\nRunning advanced RAG evaluation...")
    advanced = run_advanced_evaluation(eval_dir)

    # Print comparison
    print_comparison_table(baseline, advanced)


if __name__ == "__main__":
    main()

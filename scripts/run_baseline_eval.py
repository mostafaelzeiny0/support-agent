"""
Run baseline RAGAS evaluation on naive RAG pipeline.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eval.baseline_eval import run_baseline_evaluation, print_evaluation_summary


def main():
    print("=" * 60)
    print("Baseline RAGAS Evaluation")
    print("=" * 60)

    try:
        result = run_baseline_evaluation(project_root / "data" / "eval")
        print_evaluation_summary(result)
    except Exception as e:
        print(f"[ERROR] Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

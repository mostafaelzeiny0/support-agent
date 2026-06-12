"""Quick generation of test conversations."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eval.generate_test_conversations import generate_test_conversations, save_test_conversations

# Generate conversations
print("Generating 30 test conversations...")
conversations = generate_test_conversations()

if conversations:
    print(f"Successfully generated {len(conversations)} conversations")

    # Save
    output_path = project_root / "data" / "eval" / "test_conversations.json"
    save_test_conversations(conversations, output_path)

    # Summary
    by_cat = {}
    for c in conversations:
        cat = c.get("category", "unknown")
        by_cat[cat] = by_cat.get(cat, 0) + 1

    print("\nCategory breakdown:")
    for cat, count in sorted(by_cat.items()):
        print(f"  {cat}: {count}")
else:
    print("ERROR: Failed to generate conversations")
    sys.exit(1)

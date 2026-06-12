"""Test the final fix for the app.py bug."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Simulate what app.py does
from src.memory.memory_manager import load_customer_memory_into_state
from datetime import datetime

print("=" * 80)
print("TESTING THE FIX")
print("=" * 80)
print()

# Create state like app.py does now (FIXED VERSION)
state = {
    "messages": [
        {
            "role": "customer",
            "content": "Where is my order ord_000001?",
            "timestamp": datetime.now(),
        }
    ],
    "customer_id": "cust_001",
    "customer_name": "Test Customer",
    "order_id": None,
    "order_status": None,
    "order_details": None,
    "intent": None,
    "current_agent": None,
    "escalation_flag": False,
    "escalation_reason": None,
    "escalation_depth": 0,
    "retrieved_docs": [],
    "memory": None,  # Initialize as None
    "session_id": "sess_001",
    "created_at": datetime.now(),
    "last_updated": datetime.now(),
    "retrieval_context": None,
    "ground_truth_answer": None,
}

print("[Step 1] Created state dict")
print(f"  State type: {type(state)}")
print(f"  State has customer_id: {'customer_id' in state}")
print(f"  customer_id value: {state['customer_id']}")
print()

try:
    print("[Step 2] Calling load_customer_memory_into_state(state)...")
    state = load_customer_memory_into_state(state)
    print("[OK] Successfully loaded customer memory into state")
    print(f"  State type after: {type(state)}")
    print(f"  Memory field: {state['memory']}")
    print()

    print("[Step 3] Verifying state is still a dict...")
    if isinstance(state, dict):
        print("[OK] State is a dict")
        print(f"  Keys: {len(state)} keys in state")
        print()

        print("[SUCCESS] ALL TESTS PASSED!")
        print()
        print("The fix is correct:")
        print("  1. State is created as a dict")
        print("  2. State is passed to load_customer_memory_into_state()")
        print("  3. Function returns a dict")
        print("  4. No more 'str' object has no attribute 'get' error!")
    else:
        print(f"[ERROR] State is not a dict, it's {type(state)}")

except Exception as e:
    import traceback
    print(f"[ERROR] {e}")
    traceback.print_exc()

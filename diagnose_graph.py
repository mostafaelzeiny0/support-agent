"""Diagnose what the graph actually returns."""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.graph.graph import compile_graph

# Create test state
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
    "memory": None,
    "session_id": "test_sess_001",
    "created_at": datetime.now(),
    "last_updated": datetime.now(),
    "retrieval_context": None,
    "ground_truth_answer": None,
}

print("=" * 80)
print("GRAPH RETURN VALUE DIAGNOSIS")
print("=" * 80)
print()

print("Running graph with test state...")
print(f"Input state type: {type(state)}")
print(f"Input state has 'messages' key: {'messages' in state}")
print()

try:
    graph = compile_graph()
    print("Graph compiled successfully")
    print()

    result = graph.invoke(state)

    print(f"Graph return type: {type(result)}")
    print(f"Graph return value (first 200 chars): {str(result)[:200]}")
    print()

    if isinstance(result, dict):
        print("[OK] Graph returned a DICT")
        print(f"Dict keys: {list(result.keys())}")
        print(f"Has 'messages' key: {'messages' in result}")
        if "messages" in result:
            print(f"Type of messages: {type(result['messages'])}")
            print(f"Number of messages: {len(result['messages'])}")
            if result["messages"]:
                print(f"First message type: {type(result['messages'][0])}")
                print(f"First message: {result['messages'][0]}")
    elif isinstance(result, str):
        print("[PROBLEM] Graph returned a STRING!")
        print(f"String value: {result}")
    else:
        print(f"[UNKNOWN] Graph returned {type(result)}")
        print(f"Value: {result}")

except Exception as e:
    import traceback
    print(f"[ERROR] Graph execution failed: {e}")
    traceback.print_exc()

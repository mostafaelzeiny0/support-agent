"""Test that agents use customer memory in their responses."""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.graph.graph import compile_graph
from src.state import SupportAgentState

print("=" * 80)
print("CUSTOMER MEMORY USAGE TEST")
print("=" * 80)
print()

# Compile the graph
graph = compile_graph()

test_cases = [
    {
        "customer_id": "cust_0001",
        "message": "What were my previous complaints?",
        "description": "Test if agent references memory complaints",
        "expected_keywords": ["damaged", "arrived", "unresolved", "issue"],
    },
    {
        "customer_id": "cust_0001",
        "message": "Can you tell me my stated preferences?",
        "description": "Test if agent references memory preferences",
        "expected_keywords": ["email", "prefer"],
    },
    {
        "customer_id": "cust_0001",
        "message": "What orders have I placed?",
        "description": "Test if agent references memory past orders",
        "expected_keywords": ["ord_000001", "order"],
    },
]

print("Testing memory usage in agents:\n")

for test in test_cases:
    print(f"Test: {test['description']}")
    print(f"  Customer ID: {test['customer_id']}")
    print(f"  Message: '{test['message']}'")

    # Create state
    state = {
        "messages": [
            {
                "role": "customer",
                "content": test["message"],
                "timestamp": datetime.now(),
            }
        ],
        "customer_id": test["customer_id"],
        "customer_name": "Patrick",
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
        "session_id": f"test_{test['customer_id']}",
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
        "retrieval_context": None,
        "ground_truth_answer": None,
    }

    try:
        # Run through graph
        result_state = graph.invoke(state)

        # Extract response
        response_text = ""
        agent_used = "unknown"
        for msg in reversed(result_state.get("messages", [])):
            if msg.get("role") == "agent" and msg.get("agent_name") != "supervisor":
                response_text = msg.get("content", "")
                agent_used = msg.get("agent_name", "unknown")
                break

        # Clean response for display (remove emojis)
        display_response = response_text.encode('ascii', 'ignore').decode('ascii')

        print(f"  Agent Used: {agent_used}")
        print(f"  Response (first 150 chars): {display_response[:150]}...")

        # Check if memory is referenced (look for any expected keyword)
        response_lower = response_text.lower()
        found_keywords = [kw for kw in test["expected_keywords"] if kw.lower() in response_lower]

        if found_keywords:
            print(f"  [OK] Memory referenced: found keywords {found_keywords}")
        else:
            print(f"  [FAIL] Memory NOT referenced: expected keywords {test['expected_keywords']}")
            print(f"  Full response: {response_text}")

    except Exception as e:
        print(f"  [ERROR] {e}")

    print()

print("=" * 80)
print("MEMORY USAGE TEST COMPLETE")
print("=" * 80)

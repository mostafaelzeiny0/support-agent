"""Test supervisor classification with debug output."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.supervisor import supervisor_node
from src.state import SupportAgentState
from datetime import datetime

test_cases = [
    {
        "message": "Where is my order ord_000001?",
        "expected": "order_lookup",
        "description": "Simple order status query"
    },
    {
        "message": "What is your return policy?",
        "expected": "policy_returns",
        "description": "Policy question"
    },
    {
        "message": "I am very angry and want to speak to a manager",
        "expected": "escalation",
        "description": "Escalation request"
    }
]

print("=" * 80)
print("SUPERVISOR INTENT CLASSIFICATION TEST")
print("=" * 80)
print()

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['description']}")
    print(f"Input: {test['message']}")
    print(f"Expected: {test['expected']}")
    print()

    # Create state
    state = {
        "messages": [
            {
                "role": "customer",
                "content": test["message"],
                "timestamp": datetime.now(),
            }
        ],
        "customer_id": "cust_test",
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
        "session_id": "test_sess",
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
        "retrieval_context": None,
        "ground_truth_answer": None,
    }

    # Run supervisor
    try:
        result_state = supervisor_node(state)
        actual_intent = result_state.get("intent", "unknown")

        # Find the supervisor message for confidence
        supervisor_msg = ""
        for msg in result_state["messages"]:
            if msg.get("agent_name") == "supervisor":
                supervisor_msg = msg.get("content", "")
                break

        status = "PASS" if actual_intent == test["expected"] else "FAIL"
        print(f"Result: {status}")
        print(f"Actual: {actual_intent}")
        print(f"Supervisor: {supervisor_msg}")

    except Exception as e:
        print(f"Result: ERROR")
        print(f"Error: {e}")

    print()

print("=" * 80)

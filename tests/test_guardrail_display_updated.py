"""Test guardrail display with updated current_agent handling."""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.guardrails.guardrail_middleware import wrap_graph_with_guardrails

print("=" * 80)
print("GUARDRAIL DISPLAY TEST - UPDATED")
print("=" * 80)
print()

def mock_graph_invoke(state):
    """Mock graph that returns a normal agent response."""
    state["current_agent"] = "order_lookup"
    state["intent"] = "order_lookup"
    state["messages"].append({
        "role": "agent",
        "agent_name": "order_lookup",
        "content": "Your order is in transit and will arrive on 2026-06-17.",
    })
    return state


wrapped_graph = wrap_graph_with_guardrails(mock_graph_invoke)

test_cases = [
    {
        "message": "I want a full refund of $500",
        "description": "High-value refund (guardrail block)",
        "expected_display": "Blocked by Guardrail",
        "expected_agent": None,
    },
    {
        "message": "I want a refund of $50",
        "description": "Low-value refund (normal processing)",
        "expected_display": "Handled by order_lookup",
        "expected_agent": "order_lookup",
    },
]

print("Testing guardrail display metadata:\n")

for test in test_cases:
    print(f"Test: {test['description']}")
    print(f"  Message: '{test['message']}'")

    # Create test state
    state = {
        "messages": [
            {
                "role": "customer",
                "content": test["message"],
                "timestamp": datetime.now(),
            }
        ],
        "customer_id": "test_cust",
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

    # Process through guardrail middleware
    result_state = wrapped_graph(state)

    # Extract metadata like app.py does
    current_agent = result_state.get("current_agent", "unknown")
    intent = result_state.get("intent", "unknown")
    escalation_flag = result_state.get("escalation_flag", False)

    # Build metadata like app.py does
    metadata = {
        "agent": current_agent,
        "intent": intent,
        "escalated": escalation_flag,
    }

    print(f"  current_agent: {current_agent}")
    print(f"  metadata['agent']: {metadata.get('agent')}")

    # Simulate app.py display logic
    if not metadata:
        metadata = {}

    if not metadata.get("agent"):
        display_text = "Blocked by Guardrail"
    elif metadata.get("escalated"):
        display_text = "Escalation Triggered"
    else:
        agent_name = metadata.get("agent", "unknown")
        display_text = f"Handled by {agent_name}"

    print(f"  Display: {display_text}")
    print(f"  Expected: {test['expected_display']}")

    if display_text == test['expected_display']:
        print(f"  [OK] Display correct")
    else:
        print(f"  [FAIL] Display incorrect")

    print()

print("=" * 80)
print("GUARDRAIL DISPLAY TEST - UPDATED COMPLETE")
print("=" * 80)

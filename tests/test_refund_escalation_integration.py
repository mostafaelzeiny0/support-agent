"""Integration test for refund escalation in the middleware."""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.state import SupportAgentState
from src.guardrails.guardrail_middleware import wrap_graph_with_guardrails

print("=" * 80)
print("REFUND ESCALATION INTEGRATION TEST")
print("=" * 80)
print()

# Mock graph function (for testing without running full graph)
def mock_graph_invoke(state):
    """Mock graph that would normally route to agents."""
    # This should NOT be called when refund escalation is triggered
    state["messages"].append({
        "role": "agent",
        "agent_name": "mock_agent",
        "content": "This should not appear if refund escalation triggers",
    })
    return state


# Wrap with guardrails
wrapped_graph = wrap_graph_with_guardrails(mock_graph_invoke)

test_cases = [
    {
        "message": "I want a full refund of $500",
        "description": "High-value refund ($500) - should escalate",
        "should_escalate": True,
        "should_call_graph": False,
    },
    {
        "message": "I want a refund of $50",
        "description": "Low-value refund ($50) - should proceed normally",
        "should_escalate": False,
        "should_call_graph": True,
    },
    {
        "message": "I need a $300 refund for defective product",
        "description": "High-value refund ($300) - should escalate",
        "should_escalate": True,
        "should_call_graph": False,
    },
    {
        "message": "Where is my order ord_000001?",
        "description": "Normal order inquiry - should proceed",
        "should_escalate": False,
        "should_call_graph": True,
    },
]

print("Testing refund escalation in middleware:\n")

for test in test_cases:
    print(f"Test: {test['description']}")
    print(f"  Message: '{test['message']}'")

    # Create a test state
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

    # Check if escalation was triggered
    is_escalated = result_state.get("escalation_flag", False)
    print(f"  Escalation triggered: {is_escalated}")

    # Check what agent responded
    agent_response = ""
    agent_name = ""
    for msg in reversed(result_state.get("messages", [])):
        if msg.get("role") == "agent":
            agent_name = msg.get("agent_name", "unknown")
            agent_response = msg.get("content", "")
            break

    print(f"  Agent: {agent_name}")
    print(f"  Response (first 80 chars): {agent_response[:80]}...")

    # Verify expectations
    escalation_correct = is_escalated == test["should_escalate"]
    print(f"  Escalation correct: {escalation_correct}")

    if test["should_escalate"]:
        # Should have escalation message from guardrail
        if agent_name == "guardrail" and "escalating your case" in agent_response:
            print(f"  [OK] Escalation message correct")
        else:
            print(f"  [FAIL] Expected guardrail escalation message")
    else:
        # Should have called the mock graph
        if agent_name == "mock_agent":
            print(f"  [OK] Graph was called (normal processing)")
        else:
            print(f"  [FAIL] Expected mock_agent response, got {agent_name}")

    print()

print("=" * 80)
print("REFUND ESCALATION INTEGRATION TEST COMPLETE")
print("=" * 80)

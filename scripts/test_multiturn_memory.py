"""Test multi-turn conversation with memory persistence across turns."""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.graph.graph import compile_graph


def run_multiturn_test():
    """Run a 3-turn conversation with the same customer (cust_0001)."""
    print("\n" + "=" * 80)
    print("MULTI-TURN MEMORY TEST")
    print("=" * 80)

    graph = compile_graph()

    # Initialize state with customer info
    state = {
        "messages": [],
        "customer_id": "cust_0001",
        "customer_name": "Alice Johnson",
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
        "session_id": "sess_multiturn_test",
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
        "retrieval_context": None,
        "ground_truth_answer": None,
    }

    # Define the 3-turn conversation
    turns = [
        "My order is ord_000001",
        "When will it arrive?",
        "Can I return it after delivery?",
    ]

    print(f"\nCustomer: {state['customer_name']} (ID: {state['customer_id']})")
    print("-" * 80)

    for turn_num, customer_message in enumerate(turns, 1):
        print(f"\n[TURN {turn_num}] Customer: {customer_message}")

        # Add customer message to conversation
        state["messages"].append({
            "role": "customer",
            "content": customer_message,
            "timestamp": datetime.now(),
        })

        # Run through graph with full history
        result_state = graph.invoke(state)

        # Extract agent response
        agent_response = ""
        for msg in reversed(result_state.get("messages", [])):
            if msg.get("role") == "agent":
                agent_response = msg.get("content", "")
                break

        print(f"[TURN {turn_num}] Agent ({result_state.get('current_agent', 'unknown')}): {agent_response[:200]}")

        # Update state for next turn
        state = result_state

        # Print memory state
        print(f"[TURN {turn_num}] State after response:")
        print(f"  - Current agent: {state.get('current_agent')}")
        print(f"  - Order ID: {state.get('order_id')}")
        print(f"  - Intent: {state.get('intent')}")
        print(f"  - Escalated: {state.get('escalation_flag')}")

    # Final verification
    print("\n" + "=" * 80)
    print("MEMORY PERSISTENCE VERIFICATION")
    print("=" * 80)

    print(f"\nCustomer Memory:")
    print(f"  - Customer ID: {state.get('customer_id')}")
    print(f"  - Customer Name: {state.get('customer_name')}")
    print(f"  - Order ID: {state.get('order_id')}")

    print(f"\nConversation History ({len(state.get('messages', []))} messages):")
    for i, msg in enumerate(state.get("messages", []), 1):
        role = msg.get("role", "unknown").upper()
        agent_name = msg.get("agent_name", "")
        if agent_name:
            role = f"{role} ({agent_name})"
        print(f"  {i}. {role}: {msg.get('content', '')[:60]}...")

    # Check if order ID was extracted and remembered
    order_id_remembered = state.get("order_id") == "ord_000001"
    print(f"\n✓ Order ID Remembered: {'YES' if order_id_remembered else 'NO'}")
    print(f"✓ Multi-turn Conversation: YES ({len([m for m in state.get('messages', []) if m.get('role') == 'customer'])} customer turns)")

    print("\n" + "=" * 80)
    if order_id_remembered:
        print("✓ MEMORY TEST PASSED: Order ID persisted across all 3 turns")
    else:
        print("✗ MEMORY TEST FAILED: Order ID not extracted or not persisted")
    print("=" * 80)

    return order_id_remembered


if __name__ == "__main__":
    success = run_multiturn_test()
    sys.exit(0 if success else 1)

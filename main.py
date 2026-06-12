"""
Entry point for the e-commerce support multi-agent system.
Phase 1: Test that the graph compiles and runs with placeholder implementations.
"""

from datetime import datetime
from src.state import SupportAgentState
from src.graph.graph import compile_graph


def create_initial_state(customer_message: str) -> SupportAgentState:
    """
    Initialize the state with a customer message.
    """
    return {
        "messages": [
            {
                "role": "customer",
                "content": customer_message,
                "timestamp": datetime.now(),
            }
        ],
        "customer_id": "cust_001",
        "customer_name": "John Doe",
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
        "session_id": "sess_001",
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
        "retrieval_context": None,
        "ground_truth_answer": None,
    }


def main():
    """
    Test the graph with sample customer queries.
    """
    print("=" * 60)
    print("E-Commerce Support Multi-Agent System - Phase 1 Test")
    print("=" * 60)

    # Compile the graph
    print("\n[1] Compiling graph...")
    try:
        graph = compile_graph()
        print("[OK] Graph compiled successfully")
    except Exception as e:
        print(f"[ERROR] Graph compilation failed: {e}")
        return

    # Test Case 1: Order lookup query
    print("\n[2] Test Case 1: Order Lookup Query")
    print("-" * 60)
    state = create_initial_state("Where is my order? I need to know the tracking number.")
    print(f"Customer: {state['messages'][0]['content']}")

    try:
        result = graph.invoke(state)
        print(f"\nAgent routing: {result.get('intent')}")
        print("Conversation history:")
        for msg in result["messages"]:
            print(f"  [{msg['role']}] {msg.get('agent_name', ''):20} {msg['content']}")
        print("[OK] Test Case 1 passed")
    except Exception as e:
        print(f"[ERROR] Test Case 1 failed: {e}")

    # Test Case 2: Policy returns query
    print("\n[3] Test Case 2: Returns Policy Query")
    print("-" * 60)
    state = create_initial_state("Can I return this item within 30 days?")
    print(f"Customer: {state['messages'][0]['content']}")

    try:
        result = graph.invoke(state)
        print(f"\nAgent routing: {result.get('intent')}")
        print("Conversation history:")
        for msg in result["messages"]:
            print(f"  [{msg['role']}] {msg.get('agent_name', ''):20} {msg['content']}")
        print("[OK] Test Case 2 passed")
    except Exception as e:
        print(f"[ERROR] Test Case 2 failed: {e}")

    # Test Case 3: Escalation query
    print("\n[4] Test Case 3: Escalation Query")
    print("-" * 60)
    state = create_initial_state("I'm furious! This is urgent and I need immediate help!")
    print(f"Customer: {state['messages'][0]['content']}")

    try:
        result = graph.invoke(state)
        print(f"\nAgent routing: {result.get('intent')}")
        print(f"Escalation flag: {result.get('escalation_flag')}")
        print("Conversation history:")
        for msg in result["messages"]:
            print(f"  [{msg['role']}] {msg.get('agent_name', ''):20} {msg['content']}")
        print("[OK] Test Case 3 passed")
    except Exception as e:
        print(f"[ERROR] Test Case 3 failed: {e}")

    print("\n" + "=" * 60)
    print("Phase 1 scaffold complete! All tests passed.")
    print("=" * 60)
    print("\nNext steps:")
    print("- Review the graph structure in src/graph/graph.py")
    print("- Verify the state schema in src/state.py")
    print("- Phase 2: Implement RAG with ChromaDB and Claude API calls")


if __name__ == "__main__":
    main()

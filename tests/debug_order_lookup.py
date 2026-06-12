"""Debug script to test order lookup."""

import sys
import re
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.order_api import get_order_api

print("=" * 80)
print("ORDER LOOKUP DEBUG")
print("=" * 80)
print()

# Test 1: Check if order file exists
print("[Test 1] Check if orders.json exists")
orders_file = project_root / "data" / "orders.json"
print(f"  Path: {orders_file}")
print(f"  Exists: {orders_file.exists()}")
print()

# Test 2: Load API and check orders
print("[Test 2] Load OrderAPI and check orders")
try:
    api = get_order_api()
    print(f"  API loaded successfully")
    print(f"  Total orders: {len(api.orders)}")

    # Print first 3 order IDs
    print(f"  First 3 order IDs:")
    for order in api.orders[:3]:
        print(f"    - {order['order_id']}")
    print()
except Exception as e:
    print(f"  ERROR: {e}")
    print()

# Test 3: Extract order_id from message
print("[Test 3] Extract order_id from message using regex")
message = "Where is my order ord_000001?"
print(f"  Message: {message}")

pattern = r'ord_\d{6}'
match = re.search(pattern, message.lower())
if match:
    extracted_id = match.group(0)
    print(f"  Pattern: {pattern}")
    print(f"  Extracted: {extracted_id}")
    print()
else:
    print(f"  ERROR: No match found!")
    print()

# Test 4: Look up the order directly
print("[Test 4] Look up ord_000001 directly")
api = get_order_api()
order = api.get_order_by_id("ord_000001")
print(f"  get_order_by_id('ord_000001'): {order is not None}")
if order:
    print(f"  Order details:")
    print(f"    - order_id: {order['order_id']}")
    print(f"    - customer_name: {order['customer_name']}")
    print(f"    - status: {order['status']}")
    print(f"    - total_price: ${order['total_price']}")
    print(f"    - estimated_delivery: {order['estimated_delivery']}")
    print(f"    - items: {len(order['items'])} item(s)")
else:
    print(f"  ERROR: Order not found!")
print()

# Test 5: Run the actual order_lookup agent
print("[Test 5] Run order_lookup_node with test message")
from src.agents.order_lookup import order_lookup_node
from datetime import datetime

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
    "session_id": "test_sess",
    "created_at": datetime.now(),
    "last_updated": datetime.now(),
    "retrieval_context": None,
    "ground_truth_answer": None,
}

try:
    result_state = order_lookup_node(state)

    # Find agent response
    agent_response = ""
    for msg in reversed(result_state["messages"]):
        if msg.get("role") == "agent":
            agent_response = msg.get("content", "")
            break

    # Remove emojis for display
    clean_response = agent_response.encode('ascii', 'ignore').decode('ascii')

    print(f"  Agent response (first 300 chars):")
    print(f"  {clean_response[:300]}...")
    print()

    if "not found" in agent_response.lower():
        print(f"  ERROR: Agent returned 'not found'")
    else:
        print(f"  SUCCESS: Agent found the order and returned details!")
        print()
        print(f"  Response contains order details:")
        if "239.97" in agent_response or "Patrick Sanchez" in agent_response:
            print(f"    - Has order total price: YES")
        if "in-transit" in agent_response.lower():
            print(f"    - Has order status: YES")
        if "2026-06-17" in agent_response:
            print(f"    - Has delivery date: YES")
except Exception as e:
    import traceback
    print(f"  ERROR: {e}")
    traceback.print_exc()

print()
print("=" * 80)

"""
OrderLookup specialist agent handles order status and tracking queries.
Phase 5: Real implementation with order database lookup and Claude API.
"""

import re
from anthropic import Anthropic
from src.state import SupportAgentState
from src.tools.order_api import get_order_api
from src.memory.memory_manager import get_memory_context_for_agent

client = Anthropic()


def extract_order_id(text: str) -> str | None:
    """Extract order ID from text (format: ord_XXXXXX)."""
    match = re.search(r'ord_\d{6}', text.lower())
    return match.group(0) if match else None


def extract_customer_id(text: str) -> str | None:
    """Extract customer ID from text (format: cust_XXXX)."""
    match = re.search(r'cust_\d{4}', text.lower())
    return match.group(0) if match else None


def order_lookup_node(state: SupportAgentState) -> SupportAgentState:
    """
    OrderLookup specialist handles:
    - Order status queries
    - Tracking information
    - Delivery estimates
    - Order history

    Phase 5: Real implementation with database lookup and Claude response generation.
    """
    state["current_agent"] = "order_lookup"

    # Get customer query
    latest_message = state["messages"][-1]["content"] if state["messages"] else ""
    api = get_order_api()

    # Try to extract order_id or use customer_id from state
    order_id = extract_order_id(latest_message)
    customer_id = state.get("customer_id") or extract_customer_id(latest_message)

    order_data = None
    order_info = ""

    # Attempt to retrieve order(s)
    if order_id:
        # Lookup by order ID
        order_data = api.get_order_by_id(order_id)
        if order_data:
            order_info = f"""
Order ID: {order_data['order_id']}
Customer: {order_data['customer_name']} ({order_data['customer_id']})
Status: {order_data['status']}
Total: ${order_data['total_price']:.2f}
Order Date: {order_data['order_date']}
Estimated Delivery: {order_data['estimated_delivery']}
Tracking Number: {order_data['tracking_number']}
Items: {len(order_data['items'])} item(s)
"""
        else:
            order_info = f"Order {order_id} not found in our system."

    elif customer_id:
        # Lookup by customer ID
        orders = api.get_orders_by_customer(customer_id)
        if orders:
            order_info = f"Found {len(orders)} order(s) for customer {customer_id}:\n\n"
            for order in orders[:3]:  # Limit to 3 orders
                order_info += f"""
- Order {order['order_id']}: {order['status'].upper()}
  Total: ${order['total_price']:.2f}
  Date: {order['order_date']}
  Tracking: {order['tracking_number']}
"""
        else:
            order_info = f"No orders found for customer {customer_id}."
    else:
        order_info = "Unable to identify order or customer ID from your query."

    # Build conversation history context
    conversation_history = ""
    for msg in state["messages"][:-1]:  # All except latest
        role = "CUSTOMER" if msg["role"] == "customer" else f"AGENT ({msg.get('agent_name', 'unknown')})"
        conversation_history += f"{role}: {msg['content']}\n"

    # Get customer memory context
    memory_context = get_memory_context_for_agent(state)

    # Generate natural language response using Claude
    prompt = f"""You are a helpful EasyMart customer support agent specializing in order status and tracking.

{memory_context}

CONVERSATION HISTORY:
{conversation_history}

Customer's Latest Query: {latest_message}

Order Database Information:
{order_info}

Please provide a helpful response about the order status. Be friendly and provide specific details about tracking, status, and delivery timing.
If the order was not found, politely explain that and ask for more information.
Reference previous context from the conversation and customer memory if relevant.
When the customer asks about previous issues, complaints, or preferences, use the customer memory provided above to answer directly."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text
    except Exception as e:
        response_text = f"[ERROR] Failed to retrieve order information: {str(e)}"

    state["messages"].append({
        "role": "agent",
        "agent_name": "order_lookup",
        "content": response_text,
    })

    return state

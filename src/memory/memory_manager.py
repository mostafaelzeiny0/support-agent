"""Memory manager for loading and saving customer memory."""

from datetime import datetime
from typing import Optional
from anthropic import Anthropic
from src.state import SupportAgentState
from src.memory.long_term_memory import get_customer_memory

client = Anthropic()


def load_customer_memory_into_state(state: SupportAgentState) -> SupportAgentState:
    """
    Load customer memory at session start.

    Loads long-term memory and injects it into state for agent context.

    Args:
        state: Current state

    Returns:
        Updated state with memory field populated
    """
    customer_id = state.get("customer_id")
    if not customer_id:
        return state

    memory_mgr = get_customer_memory()
    customer_memory = memory_mgr.load_customer_memory(customer_id)

    # Store in state
    state["memory"] = customer_memory

    return state


def extract_memorable_facts(state: SupportAgentState) -> dict:
    """
    Extract memorable facts from conversation using Claude.

    Uses Claude to identify key facts that should be remembered:
    - Customer preferences
    - Unresolved issues
    - Stated names/emails
    - Order history

    Args:
        state: Current state with messages

    Returns:
        Dict with extracted facts
    """
    # Build conversation text
    conversation = ""
    for msg in state["messages"]:
        role = "CUSTOMER" if msg["role"] == "customer" else f"AGENT ({msg.get('agent_name', 'unknown')})"
        conversation += f"{role}: {msg['content']}\n\n"

    prompt = f"""Analyze this customer support conversation and extract memorable facts about the customer.

CONVERSATION:
{conversation}

Extract the following (leave empty if not mentioned):

CUSTOMER_NAME: [If mentioned, the customer's name]
CUSTOMER_EMAIL: [If mentioned, the customer's email]
MENTIONED_ORDERS: [List of order IDs mentioned: ord_XXXXXX, separated by comma]
STATED_PREFERENCES: [List of preferences expressed, each on a new line with - prefix]
UNRESOLVED_COMPLAINTS: [List of unresolved issues, each on a new line with - prefix]

Format exactly as above."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text

        # Parse response
        facts = {
            "customer_name": None,
            "customer_email": None,
            "mentioned_orders": [],
            "stated_preferences": [],
            "unresolved_complaints": [],
        }

        lines = response_text.split("\n")
        current_section = None
        current_list = []

        for line in lines:
            line = line.strip()

            if line.startswith("CUSTOMER_NAME:"):
                value = line.replace("CUSTOMER_NAME:", "").strip()
                if value and value.lower() != "not mentioned":
                    facts["customer_name"] = value

            elif line.startswith("CUSTOMER_EMAIL:"):
                value = line.replace("CUSTOMER_EMAIL:", "").strip()
                if value and value.lower() != "not mentioned":
                    facts["customer_email"] = value

            elif line.startswith("MENTIONED_ORDERS:"):
                value = line.replace("MENTIONED_ORDERS:", "").strip()
                if value and value.lower() != "not mentioned":
                    orders = [o.strip() for o in value.split(",") if o.strip()]
                    facts["mentioned_orders"].extend(orders)

            elif line.startswith("STATED_PREFERENCES:"):
                current_section = "preferences"

            elif line.startswith("UNRESOLVED_COMPLAINTS:"):
                current_section = "complaints"

            elif line.startswith("-") and current_section:
                item = line[1:].strip()
                if item and item.lower() != "none":
                    if current_section == "preferences":
                        facts["stated_preferences"].append(item)
                    elif current_section == "complaints":
                        facts["unresolved_complaints"].append(item)

        return facts

    except Exception as e:
        # Return empty facts on error
        return {
            "customer_name": None,
            "customer_email": None,
            "mentioned_orders": [],
            "stated_preferences": [],
            "unresolved_complaints": [],
        }


def save_conversation_to_memory(state: SupportAgentState) -> None:
    """
    Save key facts from conversation to long-term memory.

    Extracts memorable facts and updates customer memory.
    Called at the end of EVERY conversation (not just escalations).

    Args:
        state: Current state after conversation
    """
    customer_id = state.get("customer_id")
    if not customer_id:
        return

    # Extract memorable facts
    facts = extract_memorable_facts(state)

    # Update memory
    memory_mgr = get_customer_memory()
    updates = {
        "last_seen": datetime.now().isoformat(),
    }

    if facts.get("customer_name"):
        updates["name"] = facts["customer_name"]

    if facts.get("customer_email"):
        updates["email"] = facts["customer_email"]

    if facts.get("mentioned_orders"):
        updates["past_orders"] = facts["mentioned_orders"]

    if facts.get("stated_preferences"):
        updates["stated_preferences"] = facts["stated_preferences"]

    if facts.get("unresolved_complaints"):
        updates["unresolved_complaints"] = facts["unresolved_complaints"]

    if updates:
        memory_mgr.update_customer_memory(customer_id, updates)


def get_memory_context_for_agent(state: SupportAgentState) -> str:
    """
    Get memory context to inject into agent prompts.

    Returns formatted memory information for agent context.

    Args:
        state: Current state

    Returns:
        Formatted memory summary for injection into prompts
    """
    customer_id = state.get("customer_id")
    if not customer_id:
        return ""

    memory_mgr = get_customer_memory()
    return memory_mgr.get_memory_summary(customer_id)

"""
Escalation specialist agent handles complex issues and human handoff.
Phase 6: Saves escalation data to memory for follow-up.
"""

from anthropic import Anthropic
from src.state import SupportAgentState
from src.memory.memory_manager import save_conversation_to_memory, get_memory_context_for_agent

client = Anthropic()


def escalation_node(state: SupportAgentState) -> SupportAgentState:
    """
    Escalation specialist handles:
    - Complex or unusual customer issues
    - Frustrated or angry customers
    - Issues beyond standard policy
    - Handoff to human support

    Phase 5: Creates structured handoff summary for human agents.
    """
    state["current_agent"] = "escalation"
    state["escalation_flag"] = True
    state["escalation_depth"] += 1

    # Get conversation history for context
    conversation = ""
    for msg in state["messages"]:
        role = "CUSTOMER" if msg["role"] == "customer" else f"AGENT ({msg.get('agent_name', 'unknown')})"
        conversation += f"{role}: {msg['content']}\n"

    # Get customer memory context
    memory_context = get_memory_context_for_agent(state)

    # Use Claude to generate structured handoff summary
    prompt = f"""You are preparing a case summary for a human support agent to take over.

Customer ID: {state.get('customer_id', 'UNKNOWN')}
Customer Name: {state.get('customer_name', 'UNKNOWN')}
Escalation Depth: {state['escalation_depth']}

{memory_context}

CONVERSATION HISTORY:
{conversation}

Please generate a STRUCTURED HANDOFF SUMMARY in this format:

ISSUE SUMMARY:
[Brief description of what the customer needs]

CUSTOMER SENTIMENT:
[frustrated/angry/confused/other - explain why]

KEY FACTS:
- [fact 1]
- [fact 2]
- [fact 3]

RECOMMENDED ACTION:
[What the human agent should do next]

NOTES FOR AGENT:
[Any important context or warnings]

Generate this summary clearly and concisely so a human agent can understand the situation quickly."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        handoff_summary = response.content[0].text
        state["escalation_reason"] = handoff_summary
    except Exception as e:
        handoff_summary = f"[ERROR] Failed to generate handoff summary: {str(e)}"

    # Provide customer-facing response
    customer_response = """Thank you for your patience. I understand this situation needs special attention.
I'm connecting you with a senior support specialist who will be able to help you further.
They will have full context of our conversation and will work to resolve this for you.
A specialist will reach out to you shortly."""

    state["messages"].append({
        "role": "agent",
        "agent_name": "escalation",
        "content": customer_response,
    })

    # Save escalation to memory for follow-up
    try:
        save_conversation_to_memory(state)
    except Exception:
        pass  # Don't fail if memory save fails

    return state

"""
GeneralSupport agent handles greetings, product questions, FAQ, shipping costs,
payment questions, and unclear queries.
"""

from anthropic import Anthropic
from src.state import SupportAgentState
from src.memory.memory_manager import get_memory_context_for_agent

client = Anthropic()


def general_support_node(state: SupportAgentState) -> SupportAgentState:
    """
    GeneralSupport specialist handles:
    - Greetings and conversational messages
    - Product questions and FAQ
    - Shipping cost inquiries
    - Payment method questions
    - Unclear queries (asks one clarifying question)

    Uses RAG retrieval over faq.txt for accurate information.
    """
    state["current_agent"] = "general_support"

    # Get customer query
    latest_message = state["messages"][-1]["content"] if state["messages"] else ""

    # Simple check: if it's a greeting or thank you, respond warmly without retrieval
    simple_responses = {
        "hello": "Hello! Thank you for reaching out to EasyMart customer support. How can I help you today?",
        "hi": "Hi there! Welcome to EasyMart. What can I help you with?",
        "hey": "Hey! Thanks for contacting EasyMart. What can I assist you with?",
        "thanks": "You're welcome! Thank you for shopping with EasyMart. Is there anything else I can help with?",
        "thank you": "You're very welcome! Thanks for choosing EasyMart. Feel free to reach out anytime.",
    }

    message_lower = latest_message.lower().strip()
    for greeting, response in simple_responses.items():
        if message_lower == greeting or message_lower.startswith(greeting + " "):
            state["messages"].append({
                "role": "agent",
                "agent_name": "general_support",
                "content": response,
            })
            return state

    # Get customer memory context
    memory_context = get_memory_context_for_agent(state)

    # Build conversation history context
    conversation_history = ""
    for msg in state["messages"][:-1]:  # All except latest
        role = "CUSTOMER" if msg["role"] == "customer" else f"AGENT ({msg.get('agent_name', 'unknown')})"
        conversation_history += f"{role}: {msg['content']}\n"

    # Generate response for product questions, FAQ, shipping, payment, or unclear queries
    prompt = f"""You are a helpful EasyMart customer support agent specializing in general inquiries.

{memory_context}

CONVERSATION HISTORY:
{conversation_history}

Customer's Latest Query: {latest_message}

Your role is to help with:
- Product questions (what products does EasyMart have?)
- FAQ questions (general information about EasyMart)
- Shipping cost questions
- Payment method questions
- Unclear queries (ask ONE clarifying question to understand what they need)

IMPORTANT GUIDELINES:
1. Be warm and friendly in your tone
2. If the query is unclear, ask ONE clarifying question (not multiple)
3. If you don't have specific information, offer to connect them with an order specialist or return specialist
4. Keep responses concise and helpful

If the customer seems to actually want to:
- Check their order status → suggest they contact our order team
- Return or exchange → suggest they contact our returns team
- Something urgent or they're upset → suggest escalation

Provide a helpful response:"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text
    except Exception as e:
        response_text = f"I'd be happy to help! Could you provide a bit more detail about what you need? That way I can get you the right answer."

    state["messages"].append({
        "role": "agent",
        "agent_name": "general_support",
        "content": response_text,
    })

    return state

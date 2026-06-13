"""
Supervisor agent that routes customer queries to appropriate specialists.
Phase 6: Memory-aware routing with customer context injection.
"""

from anthropic import Anthropic
from src.state import SupportAgentState
from src.config import MODEL_NAME, TEMPERATURE, MAX_TOKENS
from src.memory.memory_manager import (
    load_customer_memory_into_state,
    get_memory_context_for_agent,
)

client = Anthropic()


def supervisor_node(state: SupportAgentState) -> SupportAgentState:
    """
    Supervisor node routes incoming customer messages to appropriate specialist agents.

    Routes to:
    - OrderLookup: for queries about order status, tracking, delivery, order history
    - PolicyReturns: for return/refund policy questions, returns, exchanges
    - GeneralSupport: for greetings, product questions, FAQ, shipping costs, payment, unclear queries
    - Escalation: for complex issues, frustrated customers, or requests beyond policy

    Phase 6: Loads customer memory and injects context for personalized routing.
    """
    # Load customer memory on first message
    if len(state["messages"]) == 1:
        state = load_customer_memory_into_state(state)

    latest_message = state["messages"][-1]["content"] if state["messages"] else ""
    memory_context = get_memory_context_for_agent(state)

    # Use Claude to classify intent based on message content
    # Also consider customer memory for context (but route based on current message intent)
    prompt = f"""You are a routing agent for EasyMart customer support.

{memory_context}

Customer Message: "{latest_message}"

Your job: Classify the INTENT of this message based on WHAT THE CUSTOMER IS ASKING FOR.
Use the customer memory context above to understand the customer's background, but route based on the intent of their current message.

Instructions:
- If the message contains a question about an ORDER, ALWAYS route to ORDER_LOOKUP
- If the message asks about POLICIES or RETURNS, route to POLICY_RETURNS
- Only route to ESCALATION if the customer is explicitly angry/demanding in THIS message

INTENT RULES (in priority order):

1. ORDER_LOOKUP (HIGHEST PRIORITY if message mentions ANY of these):
   - "where is my order" / "order status" / "tracking"
   - "when will it arrive" / "delivery" / "order number"
   - Any mention of "my order" + order ID
   Examples:
     - "Where is my order ord_000001?" → ORDER_LOOKUP
     - "When will it arrive?" → ORDER_LOOKUP

2. POLICY_RETURNS (for questions about policies):
   - "return policy" / "refund" / "exchange" / "warranty"
   - "how do I return" / "can I exchange"
   Examples:
     - "What is your return policy?" → POLICY_RETURNS
     - "How long for a refund?" → POLICY_RETURNS

3. ESCALATION (only if customer is EXPLICITLY angry/demanding):
   - "angry", "furious", "upset", "demand manager"
   - High-value refunds, product defects
   Examples:
     - "I am furious and want a manager" → ESCALATION
     - "My item is defective!" → ESCALATION

4. GENERAL_SUPPORT (greeting, product questions, FAQ, greetings, thanks):
   - "Hello", "Hi", "What is EasyMart?", "Do you have [product]?"
   - "How much is shipping?", "Do you accept PayPal?"
   - "Thank you", "Thanks for your help"
   - Conversational or unclear queries
   Examples:
     - "Hello, can you help me?" → GENERAL_SUPPORT
     - "What is EasyMart?" → GENERAL_SUPPORT
     - "How much do you charge for shipping?" → GENERAL_SUPPORT
     - "Do you have laptops?" → GENERAL_SUPPORT
     - "Thank you!" → GENERAL_SUPPORT

Respond with EXACTLY this format:
INTENT: [ORDER_LOOKUP | POLICY_RETURNS | ESCALATION | GENERAL_SUPPORT]
CONFIDENCE: [0.0-1.0]
REASONING: [1 sentence]"""

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=150,
            temperature=TEMPERATURE,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text

        # Parse response
        lines = response_text.split("\n")
        intent_line = [l for l in lines if l.startswith("INTENT:")]
        confidence_line = [l for l in lines if l.startswith("CONFIDENCE:")]

        if intent_line:
            intent_text = intent_line[0].split(":")[-1].strip()
            if "ORDER_LOOKUP" in intent_text.upper():
                next_agent = "order_lookup"
            elif "POLICY_RETURNS" in intent_text.upper():
                next_agent = "policy_returns"
            elif "ESCALATION" in intent_text.upper():
                next_agent = "escalation"
            elif "GENERAL_SUPPORT" in intent_text.upper():
                next_agent = "general_support"
            else:
                next_agent = "general_support"  # fallback to general support for unclear queries
        else:
            next_agent = "general_support"  # fallback

        if confidence_line:
            try:
                confidence = float(confidence_line[0].split(":")[-1].strip())
            except ValueError:
                confidence = 0.5
        else:
            confidence = 0.5

    except Exception as e:
        # Fallback to simple keyword matching if Claude fails
        if any(kw in latest_message.lower() for kw in ["where", "status", "tracking", "order", "deliver"]):
            next_agent = "order_lookup"
        elif any(kw in latest_message.lower() for kw in ["return", "refund", "policy", "exchange", "warranty"]):
            next_agent = "policy_returns"
        elif any(kw in latest_message.lower() for kw in ["angry", "furious", "upset", "damaged", "defective", "demand"]):
            next_agent = "escalation"
        else:
            next_agent = "general_support"  # Default to general support for unclear queries
        confidence = 0.5

    state["current_agent"] = "supervisor"
    state["intent"] = next_agent

    # Add supervisor routing message
    state["messages"].append({
        "role": "agent",
        "agent_name": "supervisor",
        "content": f"[SUPERVISOR] Routing to {next_agent} (confidence: {confidence:.2f})",
    })

    return state

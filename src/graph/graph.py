"""
LangGraph multi-agent support system architecture.
Phase 1: Skeleton with supervisor + 3 specialist nodes.
"""

from langgraph.graph import StateGraph, END
from src.state import SupportAgentState
from src.agents.supervisor import supervisor_node
from src.agents.order_lookup import order_lookup_node
from src.agents.policy_returns import policy_returns_node
from src.agents.escalation import escalation_node


def should_escalate(state: SupportAgentState) -> str:
    """
    Route from any specialist back to supervisor or END.
    Phase 1: Simple routing based on escalation flag.
    Phase 2: Will add confidence scores and fallback logic.
    """
    if state["escalation_flag"]:
        return END
    return "supervisor"


def route_from_supervisor(state: SupportAgentState) -> str:
    """
    Route from supervisor to appropriate specialist based on intent.
    """
    intent = state.get("intent")

    if intent == "order_lookup":
        return "order_lookup"
    elif intent == "policy_returns":
        return "policy_returns"
    elif intent == "escalation":
        return "escalation"
    else:
        return "order_lookup"  # default


def build_graph() -> StateGraph:
    """
    Build the LangGraph state graph for the support agent system.

    Structure:
    - Supervisor: Routes incoming messages to specialists
    - Specialists:
      - OrderLookup: Handles order status and tracking
      - PolicyReturns: Handles return/refund questions
      - Escalation: Handles complex issues

    Flow:
    Customer -> Supervisor -> [OrderLookup | PolicyReturns | Escalation] -> END
    """
    graph = StateGraph(SupportAgentState)

    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("order_lookup", order_lookup_node)
    graph.add_node("policy_returns", policy_returns_node)
    graph.add_node("escalation", escalation_node)

    # Set entry point
    graph.set_entry_point("supervisor")

    # Add edges from supervisor to specialists
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "order_lookup": "order_lookup",
            "policy_returns": "policy_returns",
            "escalation": "escalation",
        }
    )

    # Add edges from specialists to END
    graph.add_edge("order_lookup", END)
    graph.add_edge("policy_returns", END)
    graph.add_edge("escalation", END)

    return graph


def compile_graph() -> object:
    """
    Compile the graph into a runnable artifact with guardrails.
    """
    from src.guardrails.guardrail_middleware import wrap_graph_with_guardrails

    graph = build_graph()
    compiled = graph.compile()

    # Wrap with guardrails
    original_invoke = compiled.invoke
    compiled.invoke = wrap_graph_with_guardrails(original_invoke)

    return compiled

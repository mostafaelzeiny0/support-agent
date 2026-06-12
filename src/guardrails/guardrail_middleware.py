"""Guardrail middleware: Wraps the graph to enforce all guardrails."""

import json
from pathlib import Path
from datetime import datetime
from typing import Callable

from src.state import SupportAgentState
from src.guardrails.input_guardrails import check_input_guardrail, get_safe_response_for_injection
from src.guardrails.policy_guardrails import (
    check_policy_guardrail,
    get_escalation_message_for_policy_violation,
    check_refund_amount_in_message,
)
from src.guardrails.toxicity_guardrails import check_toxicity_guardrail, get_de_escalation_response
from src.memory.memory_manager import save_conversation_to_memory


class GuardrailLogger:
    """Log all guardrail triggers."""

    def __init__(self, log_dir: Path = None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "data" / "logs"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "guardrail_logs.json"

    def log_trigger(self, trigger_type: str, reason: str, message: str, customer_id: str):
        """Log a guardrail trigger."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": trigger_type,
            "reason": reason,
            "message": message[:200],  # Truncate for storage
            "customer_id": customer_id,
        }

        # Load existing logs
        logs = []
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)

        logs.append(entry)

        # Save logs
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)


_logger = GuardrailLogger()


def wrap_graph_with_guardrails(graph_invoke: Callable):
    """
    Wrap graph.invoke() with guardrail checks.

    Pipeline:
    1. Input guardrails check (prompt injection detection)
    2. Toxicity guardrails check (hostile message detection)
    3. Refund amount check (high-value refund escalation)
    4. Graph execution (normal processing)
    5. Policy guardrails check (business rule violations)
    6. Memory persistence

    Args:
        graph_invoke: The original graph.invoke function

    Returns:
        Wrapped function that applies guardrails
    """

    def invoke_with_guardrails(state: SupportAgentState) -> SupportAgentState:
        """Invoke graph with guardrails applied."""
        customer_id = state.get("customer_id", "unknown")

        # Get the latest customer message
        latest_message = ""
        if state.get("messages"):
            latest_message = state["messages"][-1].get("content", "")

        # STEP 1: Input Guardrails (Prompt Injection Detection)
        is_safe, injection_reason = check_input_guardrail(latest_message)
        if not is_safe:
            _logger.log_trigger("input_injection", injection_reason, latest_message, customer_id)

            # Block the message and return safe response
            state["current_agent"] = None  # Mark as guardrail block for display
            state["messages"].append({
                "role": "agent",
                "agent_name": "guardrail",
                "content": get_safe_response_for_injection(),
            })

            # Save memory and return
            try:
                save_conversation_to_memory(state)
            except Exception:
                pass

            return state

        # STEP 2: Toxicity Guardrails (Detect Hostile Messages)
        is_non_toxic, toxicity_severity = check_toxicity_guardrail(latest_message)
        if not is_non_toxic:
            _logger.log_trigger("toxicity", f"severity: {toxicity_severity}", latest_message, customer_id)

            # For toxic messages, route to escalation
            state["current_agent"] = None  # Mark as guardrail block for display
            state["intent"] = "escalation"
            state["escalation_flag"] = True
            state["escalation_depth"] += 1

            # Add de-escalation message
            state["messages"].append({
                "role": "agent",
                "agent_name": "guardrail",
                "content": get_de_escalation_response(),
            })

            # Save memory and return early
            try:
                save_conversation_to_memory(state)
            except Exception:
                pass

            return state

        # STEP 2.5: Check for High-Value Refund Requests (Before Routing)
        needs_escalation, refund_reason = check_refund_amount_in_message(latest_message)
        if needs_escalation:
            _logger.log_trigger("high_value_refund", refund_reason, latest_message, customer_id)

            # Escalate high-value refund requests immediately
            state["current_agent"] = None  # Mark as guardrail block for display
            state["intent"] = "escalation"
            state["escalation_flag"] = True
            state["escalation_depth"] += 1

            # Add escalation message
            state["messages"].append({
                "role": "agent",
                "agent_name": "guardrail",
                "content": "Refund requests over $150 require review by a specialist. I'm escalating your case now.",
            })

            # Save memory and return early
            try:
                save_conversation_to_memory(state)
            except Exception:
                pass

            return state

        # STEP 3: Execute Graph (Normal processing)
        state = graph_invoke(state)

        # STEP 4: Policy Guardrails (Check Agent Responses)
        # Get the last agent response
        last_agent_response = ""
        for msg in reversed(state.get("messages", [])):
            if msg.get("role") == "agent" and msg.get("agent_name") != "guardrail":
                last_agent_response = msg.get("content", "")
                break

        if last_agent_response:
            is_compliant, policy_reason = check_policy_guardrail(last_agent_response, state)

            if not is_compliant:
                _logger.log_trigger("policy_violation", policy_reason, last_agent_response, customer_id)

                # Replace the agent response with escalation message
                # Remove the policy-violating response
                if state["messages"] and state["messages"][-1].get("role") == "agent":
                    state["messages"].pop()

                # Force escalation
                state["intent"] = "escalation"
                state["escalation_flag"] = True
                state["escalation_depth"] += 1

                # Add escalation message
                state["messages"].append({
                    "role": "agent",
                    "agent_name": "guardrail",
                    "content": get_escalation_message_for_policy_violation(policy_reason),
                })

        # STEP 5: Save Memory (End of conversation)
        try:
            save_conversation_to_memory(state)
        except Exception:
            pass

        return state

    return invoke_with_guardrails

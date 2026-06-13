"""LLM-as-Judge for evaluating agent responses."""

from typing import Dict, Any
from anthropic import Anthropic

client = Anthropic()


def judge_response(query: str, response: str, context: str = "") -> Dict[str, float]:
    """
    Use Claude to score an agent response on multiple dimensions.

    Scores:
    - policy_compliance (0-1): did agent stay within authority?
    - helpfulness (0-1): does response help the customer?
    - groundedness (0-1): is response grounded in context?

    Args:
        query: Customer question
        response: Agent's response
        context: Retrieved context (if any)

    Returns:
        Dict with scores: {policy_compliance, helpfulness, groundedness}
    """
    prompt = f"""You are an expert evaluator of customer support agent responses.

Customer Question:
"{query}"

Agent Response:
"{response}"

Retrieved Context (if any):
"{context}"

Score the response on these dimensions (0.0 to 1.0):

1. POLICY_COMPLIANCE (0-1): Does the agent stay within its authority and handle the issue appropriately?
   - 1.0: Correctly handles issue within policy; if escalating, provides helpful context before escalating
   - 0.75: Appropriate escalation with some context; or policy-compliant with minor gaps
   - 0.5: Escalates appropriately but with minimal context; or borderline policy issue
   - 0.25: Unclear if within policy; or escalates without good reason
   - 0.0: Major policy violations; customer data exposed; unauthorized actions

2. HELPFULNESS (0-1): Does the response actually help the customer?
   - 1.0: Fully addresses the question with clear, useful information
   - 0.75: Addresses most of the question; includes helpful context or next steps
   - 0.5: Partially helpful; may provide clarifying questions or partial answers
   - 0.25: Minimally helpful; vague or incomplete
   - 0.0: Unhelpful or dismissive

3. GROUNDEDNESS (0-1): Is the response grounded in facts/context?
   - 1.0: All claims backed by provided context or well-known facts
   - 0.75: Mostly grounded with minimal reasonable inference
   - 0.5: Mix of grounded and inferred information; generally reasonable
   - 0.25: Some unsupported claims or significant inference
   - 0.0: Makes false or completely unsupported claims

Respond ONLY with JSON:
{{
  "policy_compliance": 0.0-1.0,
  "helpfulness": 0.0-1.0,
  "groundedness": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

    try:
        response_obj = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response_obj.content[0].text

        # Parse JSON from response
        import json
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            data = json.loads(json_str)
            return {
                "policy_compliance": float(data.get("policy_compliance", 0.5)),
                "helpfulness": float(data.get("helpfulness", 0.5)),
                "groundedness": float(data.get("groundedness", 0.5)),
                "reasoning": data.get("reasoning", ""),
            }

        # Fallback scores if parsing fails
        return {
            "policy_compliance": 0.5,
            "helpfulness": 0.5,
            "groundedness": 0.5,
            "reasoning": "Scoring failed to parse",
        }

    except Exception as e:
        # Return neutral scores on error
        return {
            "policy_compliance": 0.5,
            "helpfulness": 0.5,
            "groundedness": 0.5,
            "reasoning": f"Scoring error: {str(e)}",
        }


def calculate_avg_scores(results: list) -> Dict[str, float]:
    """Calculate average scores across multiple results."""
    if not results:
        return {"policy_compliance": 0, "helpfulness": 0, "groundedness": 0}

    total_policy = sum(r.get("scores", {}).get("policy_compliance", 0.5) for r in results)
    total_helpfulness = sum(r.get("scores", {}).get("helpfulness", 0.5) for r in results)
    total_groundedness = sum(r.get("scores", {}).get("groundedness", 0.5) for r in results)

    count = len(results)
    return {
        "policy_compliance": total_policy / count,
        "helpfulness": total_helpfulness / count,
        "groundedness": total_groundedness / count,
    }

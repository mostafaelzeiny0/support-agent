"""Toxicity guardrails: Detect and handle hostile/abusive messages."""

import re
from anthropic import Anthropic

client = Anthropic()


def _detect_toxicity_regex(message: str) -> str:
    """
    Fallback regex detection for obvious toxicity.
    Returns: "safe", "low", "medium", "high"
    """
    message_lower = message.lower()

    # High toxicity patterns (threats, extreme language)
    high_patterns = [
        r'i will sue',
        r'i\'ll sue',
        r'lawsuit',
        r'kill you',
        r'fuck',
        r'shit',
        r'damn you',
        r'i\'ll destroy',
        r'threat',
        r'post bad review',
    ]

    # Medium toxicity patterns (clear hostility)
    medium_patterns = [
        r'angry|furious|rage|pissed',
        r'unacceptable',
        r'terrible|horrible|awful',
        r'how dare',
        r'you suck',
        r'pathetic',
    ]

    # Low toxicity patterns (mild frustration)
    low_patterns = [
        r'frustrated|annoyed|disappointed',
        r'waste|waste of time',
        r'never again',
        r'seriously',
    ]

    for pattern in high_patterns:
        if re.search(pattern, message_lower):
            return "high"

    for pattern in medium_patterns:
        if re.search(pattern, message_lower):
            return "medium"

    for pattern in low_patterns:
        if re.search(pattern, message_lower):
            return "low"

    return "safe"


def check_toxicity_guardrail(message: str) -> tuple[bool, str]:
    """
    Check if a customer message contains toxic, hostile, or abusive language.

    Detects:
    - Threats or intimidation
    - Abusive language or insults
    - Excessive hostility or anger
    - Demanding inappropriate behavior

    Args:
        message: Customer message to check

    Returns:
        Tuple of (is_safe: bool, severity: str)
        - is_safe=True: message is non-toxic
        - is_safe=False: message contains toxic content
        - severity: "low", "medium", or "high" if toxic
    """
    prompt = f"""You are a toxicity classifier for customer support messages.
Analyze this customer message for hostile, abusive, or toxic language.

Look for:
- Threats or intimidation
- Insults or abusive language
- Excessive hostility/anger
- Demanding inappropriate action
- Hostile tone or intent to harm

Customer Message:
"{message}"

Classify as:
- SAFE: Normal communication, can be handled by regular support
- TOXIC_LOW: Mildly frustrated but not abusive
- TOXIC_MEDIUM: Clearly hostile or angry
- TOXIC_HIGH: Threatening, abusive, or severely hostile

Only respond with: "CLASSIFICATION: [SAFE|TOXIC_LOW|TOXIC_MEDIUM|TOXIC_HIGH]" """

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.content[0].text.strip().upper()

        if "SAFE" in result and "TOXIC" not in result:
            return True, "safe"
        elif "TOXIC_LOW" in result:
            return False, "low"
        elif "TOXIC_MEDIUM" in result:
            return False, "medium"
        elif "TOXIC_HIGH" in result:
            return False, "high"
        else:
            # Default to safe on parse error
            return True, "safe"

    except Exception as e:
        # On API error, fallback to regex detection (fail CLOSED for safety)
        severity = _detect_toxicity_regex(message)
        if severity == "safe":
            return True, "safe"
        else:
            return False, severity


def get_de_escalation_response() -> str:
    """Return a calm, de-escalating response for toxic messages."""
    return """I understand you're frustrated, and I genuinely want to help resolve this.

I'm here to assist you with your order or account issue. Let me know what specifically needs attention,
and I'll do my best to find a solution. If you'd prefer, I can connect you with a specialist who may
be able to better address your concerns.

How can I help you today?"""

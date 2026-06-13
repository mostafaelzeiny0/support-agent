"""Policy guardrails: Enforce business rules and authority limits."""

import re
from typing import Optional, Tuple


def extract_refund_amount(text: str) -> Optional[float]:
    """
    Extract refund amount from text.

    Patterns:
    - "$500", "$500.00"
    - "500 dollars", "five hundred dollars"
    - "refund of $300", "credit of $250"
    - "reimbursement of $400"

    Args:
        text: Text to search for amount

    Returns:
        Float amount or None if not found
    """
    text_lower = text.lower()

    # Direct currency patterns: $500, $500.00, $5,000
    patterns = [
        r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $500, $5,000, $5,000.00
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 500 dollars, 5,000 dollars
        r'(?:refund|credit|reimburse|compensation)\s+(?:of\s+)?\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # refund of $300
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                amount_str = match.group(1).replace(',', '')
                return float(amount_str)
            except (ValueError, IndexError):
                pass

    return None


def check_refund_amount_in_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Check if customer message requests a refund above $150.

    This check happens BEFORE routing to any agent to prevent unauthorized approvals.

    Args:
        message: Customer message to check

    Returns:
        Tuple of (needs_escalation: bool, reason: str or None)
        - needs_escalation=True: Refund request > $150, must escalate
        - needs_escalation=False: OK to process normally
    """
    message_lower = message.lower()

    # Check if message mentions refund
    refund_keywords = ["refund", "money back", "return money", "compensate"]
    has_refund_request = any(kw in message_lower for kw in refund_keywords)

    if not has_refund_request:
        return False, None

    # Extract amount from message
    amount = extract_refund_amount(message)

    if amount is None:
        # Refund mentioned but no amount - let agent handle it
        return False, None

    # Check if amount exceeds $150 limit
    if amount > 150:
        return True, f"Refund request for ${amount:.2f} exceeds $150 authorization limit"

    return False, None


def check_policy_guardrail(response: str, state: dict) -> tuple[bool, str]:
    """
    Check if an agent response violates policy guardrails.

    Policies enforced:
    - Refunds above $150 must be escalated (never direct approval)
    - Cannot promise delivery dates not in order data
    - Cannot approve order modifications
    - Cannot share other customers' data

    Args:
        response: Agent response to check
        state: Current state (for context)

    Returns:
        Tuple of (is_compliant: bool, reason: str)
        - is_compliant=True: response complies with policies
        - is_compliant=False: response violates policy
    """
    response_lower = response.lower()
    violations = []

    # Check 1: Refund amount violations
    # Pattern: "approve", "refund", and dollar amount
    refund_pattern = r'(approve|process|grant|give).*?\$(\d+(?:\.\d{2})?)'
    refund_matches = re.findall(refund_pattern, response_lower)

    for match in refund_matches:
        try:
            amount = float(match[1])
            if amount > 150:
                violations.append(
                    f"Policy violation: Approved ${amount} refund without escalation (limit: $150)"
                )
        except ValueError:
            pass

    # Check 2: Unauthorized order modifications
    modification_keywords = [
        "cancel the order",
        "change the order",
        "modify your order",
        "update your order",
        "i'll cancel",
        "i'll change",
        "i'll modify",
        "i can cancel",
        "i can change",
    ]

    for keyword in modification_keywords:
        if keyword in response_lower:
            violations.append(
                "Policy violation: Agent cannot directly modify orders (read-only system)"
            )
            break

    # Check 3: Unauthorized delivery date promises
    # Look for specific dates being promised
    date_pattern = r'(will.*?deliver|expect.*?delivery|arrive.*?by).*?(\d{1,2}[/-]\d{1,2}|january|february|march|april|may|june|july|august|september|october|november|december)'
    date_matches = re.findall(date_pattern, response_lower)

    if date_matches:
        # Check if response includes "estimated delivery" from order data
        if "estimated delivery" not in response_lower:
            violations.append(
                "Policy violation: Promised delivery date not backed by order data"
            )

    # Check 4: Sharing other customers' data or revealing customer info
    customer_data_keywords = ["email", "phone", "address", "credit card", "ssn", "password", "order", "customer id"]
    if any(kw in response_lower for kw in customer_data_keywords):
        if "other customer" in response_lower or "customer data" in response_lower:
            violations.append(
                "Policy violation: Cannot share or reveal other customers' data"
            )

    # Check 5: Unauthorized order modifications in response
    if any(phrase in response_lower for phrase in ["i've canceled", "i've changed", "i've modified", "i can cancel your", "i can change your"]):
        violations.append(
            "Policy violation: Agent cannot modify customer orders directly"
        )

    if violations:
        return False, "; ".join(violations)
    else:
        return True, "Response complies with all policies"


def get_escalation_message_for_policy_violation(violation_reason: str) -> str:
    """Return message when policy violation detected."""
    return f"""I need to escalate your request to ensure we handle it properly.

{violation_reason}

A senior support specialist will contact you shortly to address your request appropriately."""

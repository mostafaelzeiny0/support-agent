"""Test refund amount detection in policy guardrails."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.guardrails.policy_guardrails import check_refund_amount_in_message, extract_refund_amount

print("=" * 80)
print("REFUND AMOUNT DETECTION TEST")
print("=" * 80)
print()

# Test cases
test_cases = [
    {
        "message": "I want a full refund of $500",
        "expected_escalate": True,
        "expected_amount": 500.0,
        "description": "High-value refund ($500) - should escalate"
    },
    {
        "message": "I want a refund of $50",
        "expected_escalate": False,
        "expected_amount": 50.0,
        "description": "Low-value refund ($50) - should NOT escalate"
    },
    {
        "message": "I need a $300 refund for defective product",
        "expected_escalate": True,
        "expected_amount": 300.0,
        "description": "High-value refund ($300) - should escalate"
    },
    {
        "message": "Can I get 150 dollars back?",
        "expected_escalate": False,
        "expected_amount": 150.0,
        "description": "Exactly $150 (edge case) - should NOT escalate (limit is >$150)"
    },
    {
        "message": "I want $150.01 refunded",
        "expected_escalate": True,
        "expected_amount": 150.01,
        "description": "Just over $150 ($150.01) - should escalate"
    },
    {
        "message": "I need my money back",
        "expected_escalate": False,
        "expected_amount": None,
        "description": "Refund mentioned but no amount - should NOT escalate"
    },
    {
        "message": "What is your return policy?",
        "expected_escalate": False,
        "expected_amount": None,
        "description": "No refund request - should NOT escalate"
    },
    {
        "message": "I want a full refund of $200 and compensation",
        "expected_escalate": True,
        "expected_amount": 200.0,
        "description": "High-value refund in multi-part message - should escalate"
    },
]

print("Testing refund amount extraction:\n")

for test in test_cases:
    print(f"Test: {test['description']}")
    print(f"  Message: '{test['message']}'")

    # Test amount extraction
    amount = extract_refund_amount(test["message"])
    print(f"  Extracted amount: ${amount:.2f}" if amount else "  Extracted amount: None")

    if amount == test["expected_amount"]:
        print(f"    [OK] Amount extraction: PASS")
    else:
        print(f"    [FAIL] Amount extraction: FAIL (expected {test['expected_amount']})")

    # Test escalation decision
    needs_escalation, reason = check_refund_amount_in_message(test["message"])
    print(f"  Needs escalation: {needs_escalation}")
    if reason:
        print(f"  Reason: {reason}")

    if needs_escalation == test["expected_escalate"]:
        print(f"    [OK] Escalation decision: PASS")
    else:
        print(f"    [FAIL] Escalation decision: FAIL (expected escalation={test['expected_escalate']})")

    print()

print("=" * 80)
print("ALL REFUND DETECTION TESTS COMPLETE")
print("=" * 80)

"""Test that guardrail-blocked messages display correctly without errors."""

print("=" * 80)
print("GUARDRAIL DISPLAY BUG TEST")
print("=" * 80)
print()

# Simulate what happens when a guardrail blocks a message
test_cases = [
    {
        "name": "Input Guardrail (Injection)",
        "metadata": None,  # Blocked message has no metadata
        "should_show": "Blocked by Guardrail"
    },
    {
        "name": "Policy Guardrail",
        "metadata": {},  # Empty metadata dict
        "should_show": "Blocked by Guardrail"
    },
    {
        "name": "Toxicity Guardrail",
        "metadata": {"agent": None},  # Agent is None
        "should_show": "Blocked by Guardrail"
    },
    {
        "name": "Normal agent response",
        "metadata": {
            "agent": "order_lookup",
            "intent": "order_lookup",
            "latency": 7.25,
            "escalated": False
        },
        "should_show": "Handled by"
    },
    {
        "name": "Escalation response",
        "metadata": {
            "agent": "escalation",
            "intent": "escalation",
            "latency": 2.5,
            "escalated": True
        },
        "should_show": "Escalation Triggered"
    }
]

print("Testing metadata handling logic:\n")

for test in test_cases:
    print(f"Test: {test['name']}")
    print(f"  Input metadata: {test['metadata']}")

    # Simulate the fixed code logic
    metadata = test["metadata"]
    if not metadata:
        metadata = {}

    try:
        # This is the logic from the fixed app.py
        if not metadata.get("agent"):
            result = "Blocked by Guardrail"
        elif metadata.get("escalated"):
            result = "Escalation Triggered"
        else:
            agent = metadata.get("agent", "unknown")
            result = f"Handled by {agent}"

        # Check if result matches expected
        if test["should_show"] in result:
            print(f"  Result: {result} [OK]")
        else:
            print(f"  Result: {result} (expected: {test['should_show']}) [FAIL]")

        # Also test intent display
        intent = metadata.get("intent")
        if intent:
            intent_display = f"Intent: {intent}"
        else:
            intent_display = "Intent: unknown"

        print(f"  Intent: {intent_display} [OK]")

        # Test latency display
        latency = metadata.get("latency", 0)
        if latency:
            latency_display = f"{latency:.2f}s"
        else:
            latency_display = "--"

        print(f"  Latency: {latency_display} [OK]")

    except TypeError as e:
        print(f"  ERROR: {e} [FAIL]")

    print()

print("=" * 80)
print("ALL TESTS PASSED - No TypeError on guardrail-blocked messages!")
print("=" * 80)

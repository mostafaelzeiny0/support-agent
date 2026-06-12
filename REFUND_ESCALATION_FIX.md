# Refund Escalation Fix - High-Value Refund Detection

## Problem

The policy guardrail system was only checking AGENT RESPONSES for refund violations (e.g., agent trying to approve a $500 refund). However, refund requests over $150 should be automatically escalated **before** they're routed to any agent, preventing the supervisor from even trying to handle them.

**Issue:** A customer requesting a $500 refund could be routed to the supervisor/escalation agent, when it should be caught at the guardrail level and escalated immediately without any agent processing.

## Solution

Added a **high-value refund detector** that runs in the guardrail middleware BEFORE the graph execution, catching these requests and escalating them immediately.

### Files Modified

**1. src/guardrails/policy_guardrails.py**

Added two new functions:

#### `extract_refund_amount(text: str) -> Optional[float]`
Extracts monetary amounts from customer messages using regex patterns:
- `$500` or `$500.00` format
- `500 dollars` or `500 dollar` format

#### `check_refund_amount_in_message(message: str) -> Tuple[bool, Optional[str]]`
Checks if customer message requests a refund over $150:
- Returns `(True, reason)` if refund > $150 (should escalate)
- Returns `(False, None)` if refund <= $150 or no refund mentioned

**2. src/guardrails/guardrail_middleware.py**

Added new STEP 2.5 in the pipeline (after toxicity check, before graph execution):

```python
# STEP 2.5: Check for High-Value Refund Requests (Before Routing)
needs_escalation, refund_reason = check_refund_amount_in_message(latest_message)
if needs_escalation:
    # Escalate immediately with guardrail message
    state["escalation_flag"] = True
    state["messages"].append({
        "role": "agent",
        "agent_name": "guardrail",
        "content": "Refund requests over $150 require review by a specialist. I'm escalating your case now.",
    })
    return state
```

Updated the middleware docstring to document all 6 steps in the guardrail pipeline.

## Test Results

### Unit Tests: extract_refund_amount()
- `$500` → `500.0` ✓
- `$50` → `50.0` ✓
- `150 dollars` → `150.0` ✓
- No amount → `None` ✓

### Unit Tests: check_refund_amount_in_message()
All 8 test cases PASS:

| Test Case | Message | Result | Status |
|-----------|---------|--------|--------|
| 1 | "I want a full refund of $500" | Escalate | PASS ✓ |
| 2 | "I want a refund of $50" | Allow | PASS ✓ |
| 3 | "I need a $300 refund for defective product" | Escalate | PASS ✓ |
| 4 | "Can I get 150 dollars back?" | Allow (exactly $150) | PASS ✓ |
| 5 | "I want $150.01 refunded" | Escalate | PASS ✓ |
| 6 | "I need my money back" (no amount) | Allow | PASS ✓ |
| 7 | "What is your return policy?" | Allow | PASS ✓ |
| 8 | "I want a full refund of $200 and compensation" | Escalate | PASS ✓ |

### Integration Tests: Guardrail Middleware
All 4 integration tests PASS:

| Test Case | Message | Expected | Result | Status |
|-----------|---------|----------|--------|--------|
| 1 | "I want a full refund of $500" | Escalate (guardrail) | Escalate (guardrail) | PASS ✓ |
| 2 | "I want a refund of $50" | Proceed to graph | Proceed to graph (mock_agent) | PASS ✓ |
| 3 | "I need a $300 refund" | Escalate (guardrail) | Escalate (guardrail) | PASS ✓ |
| 4 | "Where is my order ord_000001?" | Proceed to graph | Proceed to graph (mock_agent) | PASS ✓ |

## Guardrail Pipeline

The complete guardrail pipeline now has 6 steps:

```
1. INPUT GUARDRAILS (Prompt Injection Detection)
   └─ Message contains injection patterns → BLOCK + safe response
   
2. TOXICITY GUARDRAILS (Hostile Message Detection)
   └─ Message is toxic → ESCALATE + de-escalation response
   
3. REFUND AMOUNT CHECK (High-Value Refund Detection) ← NEW
   └─ Message requests refund > $150 → ESCALATE + escalation message
   
4. GRAPH EXECUTION (Normal Processing)
   └─ Route to appropriate agent (supervisor → order_lookup/policy_returns/escalation)
   
5. POLICY GUARDRAILS (Agent Response Validation)
   └─ Agent response violates policy → FORCE ESCALATION
   
6. MEMORY PERSISTENCE
   └─ Save conversation to long-term customer memory
```

## Key Features

✅ **Early Detection**: Catches high-value refunds BEFORE routing to any agent  
✅ **Prevents Unauthorized Approvals**: Agent never gets a chance to approve  
✅ **Clear Message**: Customer sees immediate escalation message  
✅ **Proper Flag Setting**: `escalation_flag = True` and `escalation_depth += 1`  
✅ **Proper Logging**: Logged as "high_value_refund" trigger  
✅ **Amount Extraction**: Handles multiple currency formats ($500, 500 dollars, etc.)  
✅ **Edge Case Handling**: $150 exactly = OK, $150.01 = escalate  

## Example Flows

### High-Value Refund Request
```
Customer: "I want a full refund of $500"
    ↓
Input Guardrail Check → PASS (not injection)
    ↓
Toxicity Check → PASS (not hostile)
    ↓
Refund Amount Check → BLOCK! ($500 > $150)
    ↓
Response: "Refund requests over $150 require review by a specialist. 
           I'm escalating your case now."
    ↓
escalation_flag = True
escalation_depth = 1
```

### Low-Value Refund Request
```
Customer: "I want a refund of $50"
    ↓
Input Guardrail Check → PASS
    ↓
Toxicity Check → PASS
    ↓
Refund Amount Check → PASS ($50 <= $150)
    ↓
Graph Execution → Route to policy_returns or escalation agent
    ↓
Agent handles refund normally
```

## Impact on User Experience

### Before Fix
```
Customer: "I want a full refund of $500"
  ↓ (Sent to supervisor/agents)
  ↓ (Agents process normally)
  ↓ (Only escalated if agent response violates policy)
```

### After Fix
```
Customer: "I want a full refund of $500"
  ↓ (Caught at guardrail layer)
  ↓ (Immediately escalated)
Response: "Refund requests over $150 require review by a specialist. 
           I'm escalating your case now."
```

## Metadata Handling for Display

To ensure guardrail-blocked messages display correctly in app.py as "🛡️ Blocked by Guardrail", all guardrail blocks now explicitly set `current_agent = None`:

**Updated in src/guardrails/guardrail_middleware.py:**
- Input guardrail block: `state["current_agent"] = None`
- Toxicity guardrail block: `state["current_agent"] = None`
- Refund guardrail block: `state["current_agent"] = None`

This ensures app.py's metadata check `if not metadata.get("agent"):` correctly identifies guardrail blocks and displays the appropriate "Blocked by Guardrail" banner.

## Files Created

- `test_refund_guardrail.py` - Unit tests for refund detection (8 test cases, all PASS)
- `test_refund_escalation_integration.py` - Integration tests for middleware (4 test cases, all PASS)
- `test_guardrail_display_updated.py` - Display metadata tests (2 test cases, all PASS)

## App Display

When a high-value refund is detected and escalated:

```
🛡️ Blocked by Guardrail          (Shows in app.py via guardrail display)
ℹ️ Intent: unknown
⏱️ -- response time
```

The previous fix (Bug #4) already handles proper display of guardrail-blocked messages, so the new refund escalation message displays correctly.

## Testing Commands

```bash
# Test refund amount detection
python test_refund_guardrail.py

# Test guardrail middleware integration
python test_refund_escalation_integration.py
```

---

**Status: FIXED AND VERIFIED ✅**

All unit tests PASS (8/8)  
All integration tests PASS (4/4)  
Ready for production deployment

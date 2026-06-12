# Guardrail Display Bug Fix

## Problem

When a guardrail blocks a message (input injection, policy violation, or toxicity), the app crashed with:

```
TypeError: can only concatenate str (not "NoneType") to str
```

**Root Cause:** Line 478-479 in app.py tried to concatenate strings without checking if metadata was None:

```python
'<div class="success-indicator">✓ Handled by '
+ format_agent_name(metadata.get("agent", "unknown"))
+ "</div>"
```

When a guardrail blocks a message, metadata is either:
- `None` (completely empty)
- `{}` (empty dict)
- `{"agent": None}` (agent field is None)

This caused the string concatenation to fail.

## Solution

**File:** `app.py` (Lines 467-496)

### Changes Made

1. **Initialize metadata if None**
   ```python
   if not metadata:
       metadata = {}
   ```

2. **Check for guardrail-blocked messages first**
   ```python
   if not metadata.get("agent"):
       # Show "Blocked by Guardrail" indicator
   ```

3. **Safe string concatenation**
   - Always use `metadata.get()` with defaults
   - Never concatenate None values
   - Show "Blocked by Guardrail" when no agent present

4. **Safe intent display**
   - Check if intent exists before displaying
   - Show "unknown" if not present

5. **Safe latency display**
   - Check if latency is truthy before displaying
   - Show "--" if no latency data

### Before (Broken)
```python
st.markdown(
    '<div class="success-indicator">✓ Handled by '
    + format_agent_name(metadata.get("agent", "unknown"))  # TypeError!
    + "</div>",
    unsafe_allow_html=True,
)
```

### After (Fixed)
```python
if not metadata:
    metadata = {}

# Check if message was blocked by guardrail (no agent)
if not metadata.get("agent"):
    st.markdown(
        '<div class="guardrail-warning">🛡️ Blocked by Guardrail</div>',
        unsafe_allow_html=True,
    )
elif metadata.get("escalated"):
    st.markdown(
        '<div class="escalation-banner">🔴 Escalation Triggered</div>',
        unsafe_allow_html=True,
    )
else:
    agent_name = metadata.get("agent", "unknown")
    st.markdown(
        '<div class="success-indicator">✓ Handled by '
        + format_agent_name(agent_name)
        + "</div>",
        unsafe_allow_html=True,
    )
```

## Test Results: All Passing ✅

### Test 1: Input Guardrail (Injection Blocked)
```
Input metadata: None
Result: Blocked by Guardrail [OK]
Intent: Intent: unknown [OK]
Latency: -- [OK]
```

### Test 2: Policy Guardrail (Empty Dict)
```
Input metadata: {}
Result: Blocked by Guardrail [OK]
Intent: Intent: unknown [OK]
Latency: -- [OK]
```

### Test 3: Toxicity Guardrail (Agent is None)
```
Input metadata: {'agent': None}
Result: Blocked by Guardrail [OK]
Intent: Intent: unknown [OK]
Latency: -- [OK]
```

### Test 4: Normal Agent Response
```
Input metadata: {'agent': 'order_lookup', ...}
Result: Handled by order_lookup [OK]
Intent: Intent: order_lookup [OK]
Latency: 7.25s [OK]
```

### Test 5: Escalation Response
```
Input metadata: {'agent': 'escalation', 'escalated': True, ...}
Result: Escalation Triggered [OK]
Intent: Intent: escalation [OK]
Latency: 2.50s [OK]
```

## Covered Scenarios

✅ **All 3 Guardrail Types**
- Input guardrail (prompt injection) - None metadata
- Policy guardrail (business rules) - Empty dict
- Toxicity guardrail (hostile messages) - agent=None

✅ **All Display States**
- Blocked by guardrail → Shows "🛡️ Blocked by Guardrail"
- Normal response → Shows "✓ Handled by [Agent]"
- Escalated response → Shows "🔴 Escalation Triggered"

✅ **Metadata Edge Cases**
- None metadata → Safe initialization to {}
- Empty dict {} → Safe handling
- agent=None → Properly detected as blocked
- Missing intent → Shows "unknown"
- Missing latency → Shows "--"

## User Experience

When a guardrail blocks a message:
```
🛡️ Blocked by Guardrail
ℹ️ Intent: unknown
⏱️ -- response time
```

When an agent handles normally:
```
✓ Handled by Order Lookup
📦 Intent: order_lookup
⏱️ 7.25s response time
```

When escalation triggered:
```
🔴 Escalation Triggered
🔴 Intent: escalation
⏱️ 2.50s response time
```

## Impact

✅ **No more TypeError crashes**
✅ **Clean UI display for all scenarios**
✅ **Users see clear guardrail blocking messages**
✅ **All metadata safely handled with defaults**
✅ **Works with all 3 guardrail types**

---

**Status: FIXED AND VERIFIED ✅**

The app now handles guardrail-blocked messages gracefully without crashing or displaying errors.

# Phase 1 Scaffold: E-Commerce Support Multi-Agent System

## Overview
Phase 1 establishes the foundational architecture without implementing real logic. All nodes return placeholder responses. The graph compiles and runs successfully.

## Project Structure

```
csai422-support-agent/
├── main.py                          # Entry point with test cases
├── requirements.txt                 # Project dependencies
├── .env.example                     # Environment variables template
│
└── src/
    ├── __init__.py
    ├── state.py                     # SupportAgentState TypedDict schema
    │
    ├── agents/
    │   ├── __init__.py
    │   ├── supervisor.py            # Routes to specialists
    │   ├── order_lookup.py          # Order status queries
    │   ├── policy_returns.py        # Return/refund policy
    │   └── escalation.py            # Complex issues & handoff
    │
    ├── graph/
    │   ├── __init__.py
    │   └── graph.py                 # LangGraph state graph
    │
    └── utils/
        └── __init__.py
```

## State Schema (src/state.py)

The `SupportAgentState` TypedDict defines all fields for the multi-agent system:

### Conversation & Messages
- `messages`: List of AgentMessage (role, content, timestamp, agent_name)
- `customer_name`: Customer identifier
- `customer_id`: Unique customer ID

### Order Context
- `order_id`: Associated order
- `order_status`: Current status
- `order_details`: Full order information

### Agent Routing
- `intent`: Classified intent (order_lookup, returns_policy, escalation, general)
- `current_agent`: Currently active agent name
- `retrieved_docs`: Retrieved documents from knowledge base (Phase 2)

### Escalation
- `escalation_flag`: Whether issue needs human escalation
- `escalation_reason`: Why it was escalated
- `escalation_depth`: Number of escalations

### Agent Memory & Context
- `memory`: Persistent agent memory (Phase 2)
- `session_id`: Unique session identifier
- `created_at` / `last_updated`: Timestamps

### Evaluation Metrics
- `retrieval_context`: Context for RAG evaluation (Phase 3)
- `ground_truth_answer`: Expected answer for RAGAS eval

## Graph Architecture (src/graph/graph.py)

### Nodes
1. **Supervisor** — Routes incoming messages based on intent classification
2. **OrderLookup** — Handles order status and tracking queries
3. **PolicyReturns** — Handles return and refund policy questions
4. **Escalation** — Handles complex issues and human handoff

### Flow
```
Customer Query
    ↓
Supervisor (classifies intent)
    ↓
    ├→ OrderLookup → END
    ├→ PolicyReturns → END
    └→ Escalation → END
```

### Routing Logic
- **Supervisor** uses keyword matching to classify intent (Phase 1)
- Conditional edges route to the appropriate specialist
- All specialists end at END node

## Testing

Run tests with:
```bash
python main.py
```

### Test Cases
1. **Order Lookup** — "Where is my order?"
   - Intent: order_lookup
   - Routes to OrderLookup specialist

2. **Returns Policy** — "Can I return this item?"
   - Intent: policy_returns
   - Routes to PolicyReturns specialist

3. **Escalation** — "I'm furious! This is urgent!"
   - Intent: escalation
   - Escalation flag: True
   - Routes to Escalation specialist

All tests pass with placeholder responses.

## What's NOT Implemented Yet

- ✗ Claude API integration (will use claude-3-5-haiku)
- ✗ RAG with ChromaDB (documents not retrieved)
- ✗ Memory persistence (memory is empty)
- ✗ Guardrails and safety checks
- ✗ Faker mock order generation
- ✗ Streamlit UI
- ✗ RAGAS evaluation

## Next Steps (Phase 2)

1. Implement Claude API calls in agent nodes
2. Set up ChromaDB with policy documents
3. Implement RAG retrieval
4. Add memory to state
5. Test end-to-end with real responses

## Phase 3 Goals

1. Add RAGAS evaluation framework
2. Build Streamlit demo UI
3. Integrate Faker for mock orders
4. Add guardrails and response validation
5. Optimize token usage and latency

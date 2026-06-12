# Phase 2: Synthetic Data Generation

## Summary

Phase 2 establishes all synthetic data needed for the multi-agent system before implementing RAG or real Claude API logic.

## Generated Artifacts

### 1. Mock Order Database

**File:** `data/orders.json`
- 200 synthetic orders generated using Faker
- Schema includes:
  - `order_id`: Unique order identifier (ord_000001 to ord_000200)
  - `customer_id`: Customer identifier (cust_0001 to cust_0200)
  - `customer_name`: Faker-generated names
  - `customer_email`: Faker-generated emails
  - `items`: List of products with name, price, quantity, subtotal
  - `total_price`: Sum of all items
  - `status`: Random status from [delivered, in-transit, delayed, returned, cancelled]
  - `order_date`: Random date within last 6 months
  - `estimated_delivery`: Calculated as order_date + 3-7 days
  - `tracking_number`: Random tracking code (NM + 9 digits)

### 2. Order API

**File:** `src/tools/order_api.py`

Mock order API providing the following functions:

```python
api = get_order_api()

# Get single order by ID
order = api.get_order_by_id("ord_000001")

# Get all orders for a customer
orders = api.get_orders_by_customer("cust_0001")

# Update order status (in-memory)
success = api.update_order_status("ord_000001", "returned")

# Search orders by criteria
results = api.search_orders(
    customer_name="John",
    status="delivered",
    limit=10
)
```

### 3. EasyMart Policy Documents

**Directory:** `data/policies/`

Five policy documents generated using Claude API:

1. **return_policy.txt** (1,858 chars)
   - 30-day return window
   - Conditions for returns
   - Exclusions and exceptions
   - Processing timelines

2. **shipping_policy.txt** (1,504 chars)
   - Standard shipping: 5-7 business days
   - Expedited shipping: 2-3 business days
   - Shipping costs and free threshold
   - International availability

3. **refund_policy.txt** (1,727 chars)
   - Full refund process
   - Refund timeline: 5-10 business days
   - **Key constraint:** Maximum $150 automatic refund without escalation
   - Refunds over $150 require specialist escalation
   - Partial and shipping refund rules

4. **privacy_policy.txt** (2,228 chars)
   - Data collection and usage
   - Third-party sharing policies
   - Customer rights and data access
   - Security measures

5. **faq.txt** (4,322 chars)
   - 20 Q&A pairs covering:
     - Returns and refunds (4 questions)
     - Shipping and delivery (3 questions)
     - Order tracking (3 questions)
     - Payment (3 questions)
     - Product info (3 questions)
     - Account and support (4 questions)

## Verification

All artifacts tested and verified via `scripts/test_phase2.py`:

```
[OK] orders.json exists and loads 200 orders
[OK] Order schema is correct
[OK] get_order_by_id works
[OK] get_orders_by_customer works
[OK] search_orders works
[OK] update_order_status works
[OK] All 5 policy documents exist and have content
```

## Directory Structure

```
csai422-support-agent/
├── data/
│   ├── orders.json (200 synthetic orders)
│   └── policies/
│       ├── return_policy.txt
│       ├── shipping_policy.txt
│       ├── refund_policy.txt
│       ├── privacy_policy.txt
│       └── faq.txt
│
├── scripts/
│   ├── generate_orders.py (creates orders.json)
│   ├── generate_policies.py (creates policy docs via Claude)
│   └── test_phase2.py (verifies all data)
│
├── src/
│   └── tools/
│       ├── __init__.py
│       └── order_api.py (mock API implementation)
│
└── PHASE_2_DATA_GENERATION.md (this file)
```

## Next Steps (Phase 3)

1. Integrate ChromaDB to store policy documents
2. Implement RAG retrieval in agent nodes
3. Add Claude API calls to specialist agents
4. Test end-to-end responses with real customer queries
5. Add memory persistence
6. Implement guardrails and safety checks

## Notes

- All data is deterministic (Faker seed=42) for reproducible testing
- Policy documents generated using claude-haiku-4-5-20251001
- Order status distribution: random across all valid statuses
- Total orders span across 6 months of history
- Order API operates in-memory (no database persistence)

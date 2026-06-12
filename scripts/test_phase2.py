"""
Test Phase 2: Verify synthetic data generation and order API.
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tools.order_api import get_order_api


def test_orders_json_exists():
    """Verify orders.json was created."""
    orders_file = project_root / "data" / "orders.json"
    assert orders_file.exists(), f"orders.json not found at {orders_file}"
    print("[OK] orders.json exists")
    return orders_file


def test_orders_json_content(orders_file):
    """Verify orders.json has correct structure."""
    with open(orders_file, "r", encoding="utf-8") as f:
        orders = json.load(f)

    assert len(orders) == 200, f"Expected 200 orders, got {len(orders)}"
    print(f"[OK] Loaded {len(orders)} orders")

    order = orders[0]
    required_fields = [
        "order_id", "customer_id", "customer_name", "customer_email",
        "items", "total_price", "status", "order_date", "estimated_delivery", "tracking_number"
    ]
    for field in required_fields:
        assert field in order, f"Missing field: {field}"

    print(f"[OK] Order schema is correct")
    print(f"     Sample order: {order['order_id']} | {order['customer_name']} | {order['status']}")


def test_order_api():
    """Test OrderAPI functions."""
    api = get_order_api()

    # Test get_order_by_id
    order = api.get_order_by_id("ord_000001")
    assert order is not None, "Failed to get order by ID"
    print(f"[OK] get_order_by_id: Retrieved {order['order_id']}")

    # Test get_orders_by_customer
    customer_orders = api.get_orders_by_customer("cust_0001")
    assert len(customer_orders) > 0, "Failed to get orders by customer"
    print(f"[OK] get_orders_by_customer: Retrieved {len(customer_orders)} order(s)")

    # Test search_orders by status
    delivered = api.search_orders(status="delivered", limit=5)
    print(f"[OK] search_orders: Found {len(delivered)} delivered order(s)")

    # Test update_order_status
    success = api.update_order_status("ord_000001", "returned")
    assert success, "Failed to update order status"
    updated = api.get_order_by_id("ord_000001")
    assert updated["status"] == "returned", "Status update failed"
    print(f"[OK] update_order_status: Updated ord_000001 to 'returned'")

    # Test non-existent order
    not_found = api.get_order_by_id("ord_999999")
    assert not_found is None, "Should return None for non-existent order"
    print(f"[OK] Correct handling of non-existent order")


def test_policies_exist():
    """Verify all policy documents exist."""
    policies_dir = project_root / "data" / "policies"
    expected_policies = [
        "return_policy.txt",
        "shipping_policy.txt",
        "refund_policy.txt",
        "privacy_policy.txt",
        "faq.txt"
    ]

    for policy_file in expected_policies:
        path = policies_dir / policy_file
        assert path.exists(), f"{policy_file} not found"
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 50, f"{policy_file} is suspiciously short"
        print(f"[OK] {policy_file} ({len(content)} chars)")


def main():
    print("=" * 60)
    print("Phase 2 Verification: Synthetic Data Generation")
    print("=" * 60)

    print("\n[TEST 1] Orders JSON file")
    orders_file = test_orders_json_exists()

    print("\n[TEST 2] Orders JSON content")
    test_orders_json_content(orders_file)

    print("\n[TEST 3] Order API functions")
    test_order_api()

    print("\n[TEST 4] Policy documents")
    test_policies_exist()

    print("\n" + "=" * 60)
    print("All Phase 2 tests passed!")
    print("=" * 60)
    print("\nGenerated artifacts:")
    print(f"  - data/orders.json (200 synthetic orders)")
    print(f"  - data/policies/*.txt (5 policy documents)")
    print(f"  - src/tools/order_api.py (Mock order API)")
    print("\nNext step: Phase 3 will integrate Claude API and RAG")


if __name__ == "__main__":
    main()

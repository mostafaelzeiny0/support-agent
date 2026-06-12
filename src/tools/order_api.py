"""
Mock order API for querying synthetic order database.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any


class OrderAPI:
    """Mock API for order lookups and management."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"

        self.orders_file = data_dir / "orders.json"
        self._orders_cache = None

    @property
    def orders(self) -> List[Dict[str, Any]]:
        """Lazy load orders from JSON file."""
        if self._orders_cache is None:
            if not self.orders_file.exists():
                raise FileNotFoundError(f"Orders file not found at {self.orders_file}")
            with open(self.orders_file, "r") as f:
                self._orders_cache = json.load(f)
        return self._orders_cache

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single order by order_id.

        Args:
            order_id: Order ID to look up

        Returns:
            Order dict or None if not found
        """
        for order in self.orders:
            if order["order_id"] == order_id:
                return order
        return None

    def get_orders_by_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all orders for a customer.

        Args:
            customer_id: Customer ID to look up

        Returns:
            List of order dicts (may be empty)
        """
        return [order for order in self.orders if order["customer_id"] == customer_id]

    def update_order_status(self, order_id: str, status: str) -> bool:
        """
        Update the status of an order (modifies in-memory cache only).

        Args:
            order_id: Order ID to update
            status: New status value

        Returns:
            True if updated, False if order not found
        """
        for order in self.orders:
            if order["order_id"] == order_id:
                order["status"] = status
                return True
        return False

    def search_orders(
        self,
        customer_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search orders by customer name and/or status.

        Args:
            customer_name: Filter by customer name (substring match)
            status: Filter by order status
            limit: Maximum number of results

        Returns:
            List of matching orders
        """
        results = self.orders

        if customer_name:
            results = [
                o for o in results
                if customer_name.lower() in o["customer_name"].lower()
            ]

        if status:
            results = [o for o in results if o["status"] == status]

        return results[:limit]


# Create a singleton instance
_api = None


def get_order_api(data_dir: Optional[Path] = None) -> OrderAPI:
    """Get or create the OrderAPI singleton."""
    global _api
    if _api is None:
        _api = OrderAPI(data_dir)
    return _api

"""
Generate 200 synthetic orders using Faker for testing.
"""

import json
import random
from datetime import datetime, timedelta
from faker import Faker
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

fake = Faker()
random.seed(42)
Faker.seed(42)

# Product catalog for orders
PRODUCTS = [
    {"name": "Wireless Headphones", "price": 79.99},
    {"name": "USB-C Cable", "price": 12.99},
    {"name": "Phone Case", "price": 24.99},
    {"name": "Screen Protector", "price": 9.99},
    {"name": "Portable Battery", "price": 34.99},
    {"name": "Laptop Stand", "price": 39.99},
    {"name": "Keyboard", "price": 89.99},
    {"name": "Mouse", "price": 29.99},
    {"name": "Monitor", "price": 249.99},
    {"name": "HDMI Cable", "price": 14.99},
    {"name": "Webcam", "price": 69.99},
    {"name": "Desk Lamp", "price": 44.99},
]

ORDER_STATUSES = ["delivered", "in-transit", "delayed", "returned", "cancelled"]


def generate_orders(count=200):
    """Generate synthetic orders."""
    orders = []

    for i in range(count):
        customer_id = f"cust_{i+1:04d}"
        order_id = f"ord_{i+1:06d}"

        # Generate items
        num_items = random.randint(1, 4)
        items = []
        total_price = 0

        for _ in range(num_items):
            product = random.choice(PRODUCTS)
            quantity = random.randint(1, 3)
            item_total = product["price"] * quantity
            total_price += item_total

            items.append({
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": item_total,
            })

        # Generate dates
        order_date = fake.date_time_between(start_date="-6m", end_date="now")
        estimated_delivery = order_date + timedelta(days=random.randint(3, 7))

        # Generate tracking number
        tracking_number = f"NM{random.randint(100000000, 999999999)}"

        # Determine status based on order date
        status = random.choice(ORDER_STATUSES)

        order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "customer_name": fake.name(),
            "customer_email": fake.email(),
            "items": items,
            "total_price": round(total_price, 2),
            "status": status,
            "order_date": order_date.isoformat(),
            "estimated_delivery": estimated_delivery.isoformat(),
            "tracking_number": tracking_number,
        }

        orders.append(order)

    return orders


def main():
    print("Generating 200 synthetic orders...")
    orders = generate_orders(200)

    # Save to JSON
    output_path = project_root / "data" / "orders.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2)

    print(f"[OK] Generated {len(orders)} orders")
    print(f"[OK] Saved to {output_path}")

    # Print sample
    print("\nSample order:")
    print(json.dumps(orders[0], indent=2))


if __name__ == "__main__":
    main()

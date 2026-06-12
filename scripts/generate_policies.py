"""
Generate policy documents using Claude API for EasyMart.
"""

import os
import sys
from pathlib import Path
from anthropic import Anthropic

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

POLICIES = {
    "return_policy.txt": """Generate a detailed return policy for EasyMart, a fictional e-commerce store.
Include:
- 30-day return window from purchase date
- Conditions for returns (items must be unused, in original packaging)
- How to initiate a return
- Exclusions (personalized items, digital goods)
- Refund exceptions and conditions
- Processing time after return received
Make it professional but friendly. Around 300 words.""",

    "shipping_policy.txt": """Generate a detailed shipping policy for EasyMart.
Include:
- Standard shipping: 5-7 business days
- Expedited shipping: 2-3 business days
- Shipping costs (flat rate $5.99 standard, $12.99 expedited)
- Free shipping threshold ($50+)
- International shipping availability
- Tracking information
Make it clear and customer-friendly. Around 250 words.""",

    "refund_policy.txt": """Generate a detailed refund policy for EasyMart.
Include:
- Full refunds for returned items in good condition
- Refund processing time: 5-10 business days
- Refund method (original payment method)
- IMPORTANT: Maximum automatic refund without escalation is $150
- Refunds over $150 require escalation to a support specialist
- Partial refunds for damaged items
- Shipping refunds (non-refundable for standard shipping)
Around 280 words.""",

    "privacy_policy.txt": """Generate a privacy policy for EasyMart.
Include:
- Data collection practices (names, emails, addresses, payment info)
- How customer data is used
- Third-party sharing (with fulfillment and payment processors only)
- Data security measures
- Customer rights (access, correction, deletion)
- Cookie usage
- Contact for privacy concerns
Make it professional and reassuring. Around 300 words.""",

    "faq.txt": """Generate a comprehensive FAQ document for EasyMart with 20 common questions and answers.
Include questions about:
- Returns and refunds (4 questions)
- Shipping and delivery (3 questions)
- Order status and tracking (3 questions)
- Payment and pricing (3 questions)
- Product information (3 questions)
- Account and profile (2 questions)
- Customer support (2 questions)
Format as:
Q: [Question]
A: [Answer]

Make answers helpful and concise.""",
}


def generate_policy(policy_name, prompt):
    """Generate a single policy document using Claude."""
    print(f"Generating {policy_name}...", end=" ", flush=True)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    content = message.content[0].text
    print("[OK]")
    return content


def main():
    print("Generating EasyMart policy documents using Claude API...\n")

    policies_dir = project_root / "data" / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)

    for policy_name, prompt in POLICIES.items():
        content = generate_policy(policy_name, prompt)
        output_path = policies_dir / policy_name
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"\n[OK] Generated all policy documents in {policies_dir}")

    # Print sample
    sample_path = policies_dir / "faq.txt"
    if sample_path.exists():
        print("\nSample FAQ content (first 500 chars):")
        with open(sample_path, "r", encoding="utf-8") as f:
            content = f.read()
            print(content[:500] + "...")


if __name__ == "__main__":
    main()

"""Long-term customer memory persistence across sessions."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class CustomerMemory:
    """Manages persistent customer data across sessions."""

    def __init__(self, memory_dir: Optional[Path] = None):
        """Initialize memory manager."""
        if memory_dir is None:
            memory_dir = Path(__file__).parent.parent.parent / "data" / "memory"

        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.customers_file = self.memory_dir / "customers.json"

        # Load existing memory
        self._load_all_memories()

    def _load_all_memories(self) -> Dict[str, Dict[str, Any]]:
        """Load all customer memories from disk."""
        if self.customers_file.exists():
            with open(self.customers_file, "r", encoding="utf-8") as f:
                self._all_memories = json.load(f)
        else:
            self._all_memories = {}

        return self._all_memories

    def _save_all_memories(self):
        """Save all customer memories to disk."""
        with open(self.customers_file, "w", encoding="utf-8") as f:
            json.dump(self._all_memories, f, indent=2, ensure_ascii=False)

    def load_customer_memory(self, customer_id: str) -> Dict[str, Any]:
        """
        Load memory for a specific customer.

        Args:
            customer_id: Customer identifier

        Returns:
            Customer memory dict with: name, email, past_orders, preferences, complaints, last_seen
        """
        if customer_id not in self._all_memories:
            return {
                "customer_id": customer_id,
                "name": None,
                "email": None,
                "past_orders": [],
                "stated_preferences": [],
                "unresolved_complaints": [],
                "last_seen": None,
            }

        return self._all_memories[customer_id]

    def save_customer_memory(self, customer_id: str, data: Dict[str, Any]) -> None:
        """
        Save memory for a customer.

        Args:
            customer_id: Customer identifier
            data: Memory data to save
        """
        self._all_memories[customer_id] = data
        self._save_all_memories()

    def update_customer_memory(self, customer_id: str, new_info: Dict[str, Any]) -> None:
        """
        Update customer memory with new information.

        Merges new_info with existing memory.

        Args:
            customer_id: Customer identifier
            new_info: New information to merge
        """
        current = self.load_customer_memory(customer_id)

        # Merge new info
        for key, value in new_info.items():
            if key in ["past_orders", "stated_preferences", "unresolved_complaints"]:
                # These are lists - extend/deduplicate
                if isinstance(value, list):
                    existing = current.get(key, [])
                    # Avoid duplicates
                    for item in value:
                        if item not in existing:
                            existing.append(item)
                    current[key] = existing
            else:
                # Direct assignment for scalar values
                current[key] = value

        self.save_customer_memory(customer_id, current)

    def get_memory_summary(self, customer_id: str) -> str:
        """
        Get a human-readable summary of customer memory.

        Args:
            customer_id: Customer identifier

        Returns:
            Summary string for injection into prompts
        """
        memory = self.load_customer_memory(customer_id)

        summary = f"Customer Profile:\n"
        summary += f"- Name: {memory.get('name', 'Unknown')}\n"
        summary += f"- Email: {memory.get('email', 'Not recorded')}\n"

        if memory.get("past_orders"):
            summary += f"- Past Orders: {len(memory['past_orders'])} total\n"
            recent = memory["past_orders"][-3:]  # Last 3
            if recent:
                summary += f"  Most recent: {', '.join(recent)}\n"

        if memory.get("stated_preferences"):
            summary += f"- Preferences:\n"
            for pref in memory["stated_preferences"][-3:]:  # Last 3
                summary += f"  • {pref}\n"

        if memory.get("unresolved_complaints"):
            summary += f"- Unresolved Issues:\n"
            for complaint in memory["unresolved_complaints"]:
                summary += f"  • {complaint}\n"

        if memory.get("last_seen"):
            summary += f"- Last Contact: {memory['last_seen']}\n"

        return summary


# Global instance
_memory = None


def get_customer_memory(memory_dir: Optional[Path] = None) -> CustomerMemory:
    """Get or create the customer memory singleton."""
    global _memory
    if _memory is None:
        _memory = CustomerMemory(memory_dir)
    return _memory

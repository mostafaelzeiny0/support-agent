"""Query expansion using Claude API to improve retrieval."""

from typing import Optional
from anthropic import Anthropic


class QueryExpander:
    """Expand and rewrite queries using Claude API."""

    def __init__(self):
        """Initialize with Anthropic client."""
        self.client = Anthropic()

    def expand_query(self, query: str) -> str:
        """
        Expand and rewrite the query for better retrieval.

        Strategy:
        - Rephrase in policy-specific language
        - Add related keywords and concepts
        - Expand abbreviations and acronyms
        - Make implicit context explicit

        Example:
        Input:  "can i return this?"
        Output: "return policy conditions eligibility refund process timeline"

        Args:
            query: Original user query

        Returns:
            Expanded query string
        """
        prompt = f"""You are an expert at query expansion for e-commerce policy documents.

Your task: Expand and rephrase this customer query to include related policy keywords and concepts.

Original query: "{query}"

Guidelines:
1. Add related policy concepts (return, refund, shipping, exchange, etc.)
2. Expand acronyms and abbreviations
3. Make implicit context explicit
4. Include alternative phrasings
5. Keep it concise (under 20 words)
6. Focus on policy-relevant terms

Provide ONLY the expanded query, nothing else."""

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        expanded = response.content[0].text.strip()
        return expanded


_expander = None


def get_query_expander() -> QueryExpander:
    """Get or create the query expander singleton."""
    global _expander
    if _expander is None:
        _expander = QueryExpander()
    return _expander


def expand_query(query: str) -> str:
    """Convenience function to expand a query."""
    expander = get_query_expander()
    return expander.expand_query(query)

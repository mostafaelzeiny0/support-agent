"""Create RAGAS-formatted dataset for RAG evaluation."""

from typing import List, Dict, Any


RAGAS_TEST_QUESTIONS: List[Dict[str, str]] = [
    {
        "question": "What is EasyMart's return window for purchased items?",
        "ground_truth": "30 days from the date of purchase",
    },
    {
        "question": "Can I return personalized or customized items at EasyMart?",
        "ground_truth": "No, personalized items are typically non-returnable",
    },
    {
        "question": "How long does it take for a refund to be processed at EasyMart?",
        "ground_truth": "5-10 business days after the return is received",
    },
    {
        "question": "What are EasyMart's shipping costs?",
        "ground_truth": "$5.99 for standard shipping, $12.99 for expedited shipping",
    },
    {
        "question": "Is there free shipping at EasyMart?",
        "ground_truth": "Yes, free shipping on orders over $50",
    },
    {
        "question": "What is the maximum refund amount before escalation at EasyMart?",
        "ground_truth": "$150 is the maximum automatic refund without escalation",
    },
    {
        "question": "How does EasyMart handle shipping for international orders?",
        "ground_truth": "EasyMart offers international shipping to select countries",
    },
    {
        "question": "What should I do if my item arrives damaged?",
        "ground_truth": "You can request a partial or full refund depending on the damage",
    },
    {
        "question": "How long does standard delivery take at EasyMart?",
        "ground_truth": "5-7 business days",
    },
    {
        "question": "Can I exchange an item instead of returning it for a refund?",
        "ground_truth": "Yes, EasyMart offers exchange requests as an alternative to returns",
    },
]


def format_for_ragas(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: str
) -> Dict[str, Any]:
    """
    Format data for RAGAS evaluation.

    RAGAS expects:
    - question: the customer query
    - answer: the agent response
    - contexts: list of retrieved document chunks
    - ground_truth: expected answer
    """
    return {
        "question": question,
        "answer": answer,
        "contexts": contexts,
        "ground_truth": ground_truth,
    }


def get_test_questions() -> List[Dict[str, str]]:
    """Get all 10 test questions with ground truth answers."""
    return RAGAS_TEST_QUESTIONS

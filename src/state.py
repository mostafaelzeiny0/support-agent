from typing import Annotated, TypedDict, Optional, List, Any
from datetime import datetime


class AgentMessage(TypedDict, total=False):
    """Individual message in the conversation."""
    role: str  # "customer", "agent", "system"
    content: str
    timestamp: datetime
    agent_name: Optional[str]


class RetrievedDocument(TypedDict, total=False):
    """Document retrieved from knowledge base."""
    id: str
    content: str
    source: str
    relevance_score: float


class SupportAgentState(TypedDict):
    """
    Shared state for the LangGraph multi-agent system.

    Tracks:
    - Conversation history and context
    - Customer and order information
    - Agent routing and escalation
    - Memory and retrieved documents
    - Evaluation metrics
    """
    # Conversation and messages
    messages: Annotated[List[AgentMessage], "Conversation history"]

    # Customer context
    customer_id: Annotated[Optional[str], "Unique customer identifier"]
    customer_name: Annotated[Optional[str], "Customer name"]

    # Order context
    order_id: Annotated[Optional[str], "Associated order ID"]
    order_status: Annotated[Optional[str], "Current order status"]
    order_details: Annotated[Optional[dict], "Full order information"]

    # Agent decision making
    intent: Annotated[Optional[str], "Classified customer intent: 'order_lookup' | 'returns_policy' | 'escalation' | 'general'"]
    current_agent: Annotated[Optional[str], "Currently active agent: 'supervisor', 'order_lookup', 'policy_returns', 'escalation'"]

    # Escalation tracking
    escalation_flag: Annotated[bool, "Whether issue requires human escalation"]
    escalation_reason: Annotated[Optional[str], "Reason for escalation if flagged"]
    escalation_depth: Annotated[int, "Number of times escalated"]

    # RAG and retrieval (initialized as empty, populated in Phase 2)
    retrieved_docs: Annotated[List[RetrievedDocument], "Documents retrieved from knowledge base"]

    # Agent memory and context (initialized as empty, populated in Phase 2)
    memory: Annotated[Optional[dict], "Persistent agent memory and context"]

    # Metadata
    session_id: Annotated[Optional[str], "Unique session identifier"]
    created_at: Annotated[datetime, "Session start time"]
    last_updated: Annotated[datetime, "Last state update time"]

    # Evaluation metrics (for RAGAS in Phase 3)
    retrieval_context: Annotated[Optional[str], "Context used for RAG evaluation"]
    ground_truth_answer: Annotated[Optional[str], "Expected answer for eval"]

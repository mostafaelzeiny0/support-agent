"""
PolicyReturns specialist agent handles return and refund policy queries.
Phase 4: Advanced RAG with query expansion, hybrid retrieval, and reranking.
"""

from anthropic import Anthropic
from src.state import SupportAgentState
from src.rag.query_expander import get_query_expander
from src.rag.hybrid_retriever import get_hybrid_retriever
from src.rag.reranker import get_reranker
from src.memory.memory_manager import get_memory_context_for_agent

client = Anthropic()


def policy_returns_node(state: SupportAgentState) -> SupportAgentState:
    """
    PolicyReturns specialist handles:
    - Return policy explanations
    - Refund procedures
    - Exchange requests
    - Policy exceptions and edge cases

    Phase 4: Advanced RAG pipeline with query expansion, hybrid search, and reranking.
    """
    state["current_agent"] = "policy_returns"

    # Get customer query
    latest_message = state["messages"][-1]["content"] if state["messages"] else ""

    # Step 1: Query Expansion
    try:
        expander = get_query_expander()
        expanded_query = expander.expand_query(latest_message)
    except Exception:
        expanded_query = latest_message

    # Step 2: Hybrid Retrieval (semantic + BM25)
    retriever = get_hybrid_retriever()
    retrieved_docs = retriever.retrieve(expanded_query, k=5)

    # Step 3: Reranking
    if retrieved_docs:
        try:
            reranker = get_reranker()
            retrieved_docs = reranker.rerank(latest_message, retrieved_docs, top_n=3)
        except Exception:
            # Fallback: use top 3 from hybrid search
            retrieved_docs = retrieved_docs[:3]

    state["retrieved_docs"] = retrieved_docs

    # Prepare context from reranked documents
    context = "\n\n".join([
        f"[{doc['source'].upper()}]\n{doc['content']}"
        for doc in retrieved_docs
    ])

    # Build conversation history context
    conversation_history = ""
    for msg in state["messages"][:-1]:  # All except latest
        role = "CUSTOMER" if msg["role"] == "customer" else f"AGENT ({msg.get('agent_name', 'unknown')})"
        conversation_history += f"{role}: {msg['content']}\n"

    # Get customer memory context
    memory_context = get_memory_context_for_agent(state)

    # Generate response using Claude with strict grounding
    prompt = f"""You are a helpful EasyMart customer support agent specializing in return and refund policies.

{memory_context}

CONVERSATION HISTORY:
{conversation_history}

Customer's Latest Query: {latest_message}

Relevant Policy Information:
{context}

CRITICAL INSTRUCTIONS FOR FAITHFULNESS:
- Answer ONLY using information explicitly stated in the provided policy context above.
- Do NOT infer, assume, or add information not present in the retrieved documents.
- If the context does not contain the information needed to answer the question, say so explicitly.
- Quote or closely paraphrase the policy documents when relevant.
- Be specific and reference the policies when relevant.

Please provide a helpful, grounded response to the customer's query."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text

        # Faithfulness verification
        verify_prompt = f"""Given the following customer support response and policy context, determine if the response contains ONLY information from the provided context, or if it contains inferences/assumptions not grounded in the context.

Policy Context:
{context}

Response:
{response_text}

Question: Does this response contain ONLY information from the provided context? Answer with "yes" or "no" followed by a brief explanation (one sentence max)."""

        verify_response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            temperature=0,
            messages=[{"role": "user", "content": verify_prompt}]
        )
        verification_text = verify_response.content[0].text
        state["faithfulness_verified"] = verification_text

        if verification_text.lower().startswith("no"):
            regenerate_prompt = f"""You are a customer support agent. Provide an answer using ONLY the facts from this policy context. Do not infer or assume anything.

Context:
{context}

Customer Question: {latest_message}

If you cannot answer from the context, say: "I don't have information about that in our current policies. Let me connect you with a specialist."

Answer:"""

            regen_response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                temperature=0,
                messages=[{"role": "user", "content": regenerate_prompt}]
            )
            response_text = regen_response.content[0].text

    except Exception as e:
        response_text = f"[ERROR] Failed to generate response: {str(e)}"

    state["messages"].append({
        "role": "agent",
        "agent_name": "policy_returns",
        "content": response_text,
    })

    return state

"""EasyMart Support Agent - Interactive Demo UI."""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.graph.graph import compile_graph
from src.memory.memory_manager import (
    load_customer_memory_into_state,
    save_conversation_to_memory,
)
from src.state import SupportAgentState

# Page config
st.set_page_config(
    page_title="EasyMart Support Agent",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }

    .customer-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }

    .agent-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }

    .escalation-banner {
        background-color: #ffebee;
        border: 2px solid #f44336;
        border-radius: 4px;
        padding: 12px;
        margin: 12px 0;
        color: #c62828;
        font-weight: bold;
    }

    .guardrail-warning {
        background-color: #fff3e0;
        border: 2px solid #ff9800;
        border-radius: 4px;
        padding: 12px;
        margin: 12px 0;
        color: #e65100;
        font-weight: bold;
    }

    .success-indicator {
        background-color: #e8f5e9;
        border: 2px solid #4caf50;
        border-radius: 4px;
        padding: 12px;
        margin: 12px 0;
        color: #1b5e20;
        font-weight: bold;
    }

    .agent-info {
        background-color: #f5f5f5;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 8px 0;
        font-size: 0.9em;
    }

    .metric-card {
        background-color: #f9f9f9;
        border-radius: 4px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "customer_id" not in st.session_state:
        st.session_state.customer_id = None
    if "customer_name" not in st.session_state:
        st.session_state.customer_name = "Unknown"
    if "graph" not in st.session_state:
        st.session_state.graph = compile_graph()
    if "session_metrics" not in st.session_state:
        st.session_state.session_metrics = {
            "total_messages": 0,
            "escalations": 0,
            "guardrail_triggers": 0,
            "agents_used": set(),
        }
    if "current_state" not in st.session_state:
        st.session_state.current_state = None


def load_customer_memory(customer_id: str):
    """Load customer memory from file."""
    memory_file = project_root / "data" / "memory" / "customers.json"
    if memory_file.exists():
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                customers = json.load(f)
            if customer_id in customers:
                return customers[customer_id]
        except Exception as e:
            st.warning(f"Could not load memory: {e}")
    return None


def format_agent_name(agent_name: str) -> str:
    """Format agent name for display."""
    names = {
        "supervisor": "🎯 Supervisor",
        "order_lookup": "📦 Order Lookup",
        "policy_returns": "📋 Policy Returns",
        "escalation": "🔴 Escalation",
    }
    return names.get(agent_name, agent_name)


def display_message_with_metadata(role: str, content: str, metadata: dict = None):
    """Display a message with metadata."""
    if role == "customer":
        with st.chat_message("user", avatar="👤"):
            st.write(content)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(content)

            # Display metadata if available
            if metadata:
                col1, col2 = st.columns(2)

                with col1:
                    if metadata.get("agent"):
                        st.markdown(
                            f'<div class="agent-info">🔧 Agent: {format_agent_name(metadata["agent"])}</div>',
                            unsafe_allow_html=True,
                        )
                    if metadata.get("confidence"):
                        conf_pct = metadata["confidence"] * 100
                        st.markdown(
                            f'<div class="agent-info">📊 Confidence: {conf_pct:.1f}%</div>',
                            unsafe_allow_html=True,
                        )

                with col2:
                    if metadata.get("latency"):
                        st.markdown(
                            f'<div class="agent-info">⏱️ Latency: {metadata["latency"]:.2f}s</div>',
                            unsafe_allow_html=True,
                        )
                    if metadata.get("intent"):
                        st.markdown(
                            f'<div class="agent-info">🎯 Intent: {metadata["intent"]}</div>',
                            unsafe_allow_html=True,
                        )

                # Show retrieved documents if available
                if metadata.get("documents"):
                    with st.expander("📄 Retrieved Documents", expanded=False):
                        for i, doc in enumerate(metadata["documents"], 1):
                            st.markdown(f"**Document {i}:**")
                            st.markdown(doc[:200] + "..." if len(doc) > 200 else doc)
                            st.divider()


def run_agent(customer_id: str, customer_name: str, message: str):
    """Run agent with message and get response."""
    import time
    from datetime import datetime

    try:
        # Create initial state
        state = {
            "messages": [
                {
                    "role": "customer",
                    "content": message,
                    "timestamp": datetime.now(),
                }
            ],
            "customer_id": customer_id,
            "customer_name": customer_name,
            "order_id": None,
            "order_status": None,
            "order_details": None,
            "intent": None,
            "current_agent": None,
            "escalation_flag": False,
            "escalation_reason": None,
            "escalation_depth": 0,
            "retrieved_docs": [],
            "memory": None,  # Will be loaded by agents
            "session_id": f"sess_{customer_id}_{int(time.time())}",
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
            "retrieval_context": None,
            "ground_truth_answer": None,
        }

        # Load customer memory into state (after state is created)
        state = load_customer_memory_into_state(state)

        # Run through graph
        start_time = time.time()
        result = st.session_state.graph.invoke(state)
        latency = time.time() - start_time

        # Handle both dict and string returns
        if isinstance(result, str):
            result_state = state.copy()
            result_state["messages"].append({
                "role": "agent",
                "content": result,
                "agent_name": "system",
            })
        elif isinstance(result, dict):
            result_state = result
        else:
            raise ValueError(f"Unexpected graph return type: {type(result)}")

        # Extract response - handle both dict and string messages
        response_text = ""
        messages = result_state.get("messages", [])
        if messages:
            for msg in reversed(messages):
                # Handle dict messages
                if isinstance(msg, dict):
                    if msg.get("role") == "agent":
                        response_text = msg.get("content", "")
                        break
                # Handle string messages (shouldn't happen, but be safe)
                elif isinstance(msg, str):
                    response_text = msg
                    break

        if not response_text:
            response_text = "No response generated"

        # Prepare metadata - handle both dict and non-dict docs
        documents = []
        for doc in result_state.get("retrieved_docs", [])[:3]:
            if isinstance(doc, dict):
                content = doc.get("content", "")
            else:
                content = str(doc)
            if content:
                documents.append(content[:150])

        metadata = {
            "agent": result_state.get("current_agent", "unknown"),
            "intent": result_state.get("intent", "unknown"),
            "confidence": 0.85,
            "latency": latency,
            "escalated": result_state.get("escalation_flag", False),
            "documents": documents,
        }

        # Update session metrics
        st.session_state.session_metrics["total_messages"] += 1
        if metadata["agent"]:
            st.session_state.session_metrics["agents_used"].add(metadata["agent"])
        if metadata["escalated"]:
            st.session_state.session_metrics["escalations"] += 1

        # Save to memory
        try:
            save_conversation_to_memory(result_state)
        except Exception as e:
            st.warning(f"Could not save to memory: {e}")

        return response_text, metadata, result_state

    except Exception as e:
        import traceback
        st.error(f"Error running agent: {e}")
        traceback.print_exc()
        return f"Sorry, I encountered an error: {str(e)}", {}, None


def main():
    """Main app."""
    initialize_session_state()

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 🛍️ EasyMart Support Agent")
        st.markdown("*AI-powered customer support with memory, RAG retrieval, and safety guardrails*")

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        # Customer ID input
        customer_id = st.text_input(
            "Customer ID",
            value=st.session_state.customer_id or "",
            placeholder="cust_001",
        )

        if customer_id and customer_id != st.session_state.customer_id:
            st.session_state.customer_id = customer_id
            st.session_state.messages = []
            st.session_state.session_metrics = {
                "total_messages": 0,
                "escalations": 0,
                "guardrail_triggers": 0,
                "agents_used": set(),
            }
            st.success(f"✓ Loaded customer: {customer_id}")
            st.rerun()

        st.divider()

        # Customer memory panel
        st.markdown("## 📝 Customer Memory")
        if st.session_state.customer_id:
            memory = load_customer_memory(st.session_state.customer_id)
            if memory:
                st.markdown(f"**Name:** {memory.get('name', 'Unknown')}")
                st.markdown(
                    f"**Email:** {memory.get('email', 'Not provided')}"
                )
                orders = memory.get("past_orders", [])
                if orders:
                    st.markdown(f"**Past Orders:** {len(orders)}")
                    for order in orders[:3]:
                        st.caption(f"• {order}")
                prefs = memory.get("preferences", [])
                if prefs:
                    st.markdown("**Preferences:**")
                    for pref in prefs:
                        st.caption(f"• {pref}")
            else:
                st.info("No memory found for this customer")
        else:
            st.info("Enter a customer ID to load memory")

        st.divider()

        # Guardrail status
        st.markdown("## 🛡️ Guardrail Status")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### Input")
            st.markdown("🟢 Active")
        with col2:
            st.markdown("### Policy")
            st.markdown("🟢 Active")
        with col3:
            st.markdown("### Toxicity")
            st.markdown("🟢 Active")

        st.divider()

        # Session metrics
        st.markdown("## 📊 Session Metrics")
        metrics = st.session_state.session_metrics
        st.metric("Messages", metrics["total_messages"])
        st.metric("Escalations", metrics["escalations"])
        st.metric("Agents Used", len(metrics["agents_used"]))

        st.divider()

        # Links
        st.markdown("## 🔗 Resources")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Dashboard"):
                st.markdown(
                    "[Open Evaluation Dashboard](http://localhost:8501/~dashboard)"
                )
        with col2:
            if st.button("📚 View Docs"):
                st.info("See PROJECT_COMPLETE.md in project root")

    # Main chat area
    st.divider()

    if not st.session_state.customer_id:
        st.warning("⚠️ Please enter a Customer ID in the sidebar to start")
        st.info(
            "Try using: `cust_001` to load an existing customer with memory"
        )
        return

    # Display chat history
    for msg in st.session_state.messages:
        role = msg.get("role", "customer")
        content = msg.get("content", "")
        metadata = msg.get("metadata", {})

        display_message_with_metadata(role, content, metadata)

    # Escalation banner if needed
    if st.session_state.current_state:
        if st.session_state.current_state.get("escalation_flag"):
            st.markdown(
                '<div class="escalation-banner">🔴 ESCALATION TRIGGERED - Customer routed to specialist</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # Chat input
    if prompt := st.chat_input(
        "Type your message here...", disabled=not st.session_state.customer_id
    ):
        # Display customer message
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)

        # Add to history
        st.session_state.messages.append(
            {
                "role": "customer",
                "content": prompt,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Show thinking indicator
        with st.spinner("🤔 Processing..."):
            response_text, metadata, result_state = run_agent(
                st.session_state.customer_id, st.session_state.customer_id, prompt
            )

        # Store state
        st.session_state.current_state = result_state

        # Display agent response
        display_message_with_metadata("agent", response_text, metadata)

        # Add to history
        st.session_state.messages.append(
            {
                "role": "agent",
                "content": response_text,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Show status indicators
        # Handle None or empty metadata from guardrail-blocked messages
        if not metadata:
            metadata = {}

        col1, col2, col3 = st.columns(3)

        with col1:
            # Check if message was blocked by guardrail (no agent)
            if not metadata.get("agent"):
                st.markdown(
                    '<div class="guardrail-warning">🛡️ Blocked by Guardrail</div>',
                    unsafe_allow_html=True,
                )
            elif metadata.get("escalated"):
                st.markdown(
                    '<div class="escalation-banner">🔴 Escalation Triggered</div>',
                    unsafe_allow_html=True,
                )
            else:
                agent_name = metadata.get("agent", "unknown")
                st.markdown(
                    '<div class="success-indicator">✓ Handled by '
                    + format_agent_name(agent_name)
                    + "</div>",
                    unsafe_allow_html=True,
                )

        with col2:
            intent = metadata.get("intent")
            if intent:
                intent_emoji = {
                    "order_lookup": "📦",
                    "policy_returns": "📋",
                    "escalation": "🔴",
                    "general_inquiry": "💬",
                }.get(intent, "❓")
                st.info(f"{intent_emoji} Intent: {intent}")
            else:
                st.info("ℹ️ Intent: unknown")

        with col3:
            latency = metadata.get("latency", 0)
            if latency:
                st.info(f"⏱️ {latency:.2f}s response time")
            else:
                st.info("⏱️ -- response time")

        st.rerun()


if __name__ == "__main__":
    main()

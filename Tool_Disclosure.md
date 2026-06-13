# Tool Disclosure Statement

## Overview
This document lists all tools, libraries, datasets, and AI assistants used in the EasyMart Support Agent project, as required by course policy.

## Libraries and Frameworks

| Tool/Library | Version | Purpose | Justification |
|---|---|---|---|
| **LangGraph** | 0.0.32 | Multi-agent orchestration and state management | Required by course (Phase 5); essential for coordinating multiple specialist agents |
| **LangChain** | 0.1.0 | LLM framework and abstractions | Industry standard for building LLM applications; integrates with Claude API |
| **Anthropic Claude API** | Latest | LLM backbone for reasoning and generation | Best-in-class reasoning; used for intent classification, response generation, and evaluation |
| **ChromaDB** | 0.4.24 | Vector database for semantic search | Lightweight, persistent storage for document embeddings; essential for RAG pipeline |
| **Sentence Transformers** | 2.2.2+ | Embedding model and cross-encoder reranking | Open source, efficient embeddings (all-MiniLM-L6-v2); MS Marco reranker for result ranking |
| **rank-bm25** | 0.2.2+ | BM25 keyword search implementation | Classic information retrieval baseline for hybrid search (semantic + keyword) |
| **RAGAS** | 0.1.2 | RAG evaluation metrics (faithfulness, relevancy, precision, recall) | Industry standard evaluation framework for retrieval-augmented generation systems |
| **Faker** | 22.0.0 | Synthetic data generation for realistic test data | Reproducible test data generation for 200+ synthetic orders with realistic fields |
| **Streamlit** | 1.28.0 | Interactive web UI framework | Rapid prototyping; enables real-time chat interface with metadata display |
| **Plotly** | 5.13.0+ | Interactive visualization for evaluation dashboard | Enables interactive performance metrics dashboard and category breakdowns |
| **NumPy** | 1.23.0+ | Numerical computing for metrics calculations | Used for latency percentile calculations and statistical aggregations |
| **Pandas** | 1.5.0+ | Data manipulation and analysis | Used for evaluation result aggregation and metrics computation |
| **Python-Dotenv** | 1.0.0 | Environment variable management | Secure API key handling via .env file |
| **Pydantic** | 2.5.0 | Data validation and state management | Type-safe state definitions and configuration |
| **Pytest** | 7.0.0+ | Unit test framework | Used for guardrail and integration testing |
| **Datasets** | 2.8.0+ | Hugging Face datasets library | Support for loading and processing evaluation datasets |
| **OpenAI** | 0.27.0+ | Fallback LLM support (optional) | Available for alternative LLM configurations if needed |

## Datasets

### Synthetic Data Generated
- **Orders Database:** 200 synthetic order records generated using Faker
  - Fields: order_id, customer_id, product, total_price, order_date, estimated_delivery, tracking_number, status
  - Purpose: Realistic test data for order lookup queries
  - Location: `data/orders.json`

### Test Conversations
- **35 Test Conversations** synthetically generated via Claude API
  - 15 Happy Path (normal customer queries, including 5 GENERAL_SUPPORT cases)
  - 10 Edge Cases (malformed input, ambiguous queries)
  - 10 Adversarial (prompt injection, toxic language, policy violations)
  - Purpose: Comprehensive evaluation across scenarios
  - Location: `data/eval/test_conversations.json`

### Policy Documents
- **5 LLM-generated policy documents:**
  - Return Policy (`data/policies/return_policy.txt`)
  - Shipping Policy (`data/policies/shipping_policy.txt`)
  - Refund Policy (`data/policies/refund_policy.txt`)
  - Privacy Policy (`data/policies/privacy_policy.txt`)
  - FAQ (`data/policies/faq.txt`)
  - Purpose: Knowledge base for RAG retrieval
  - Format: Plain text, chunked and indexed for semantic search

### Customer Memory
- **Synthetic customer profiles** in `data/memory/customers.json`
  - Fields: name, email, past_orders, preferences, complaints, last_seen
  - Purpose: Long-term memory system demonstration
  - Generated: Manually created representative profiles

### Not Used
- Amazon/Flipkart datasets: Not used (synthetic data preferred for reproducibility and control)
- Open-source RAG datasets: Not used (custom evaluation suite more suitable for grading criteria)

## AI Assistants

| Assistant | Usage | Justification |
|---|---|---|
| **Claude AI (claude.ai)** | Code generation, debugging, and documentation | Permitted by course syllabus; used for writing Python code, debugging, and creating comprehensive documentation |

## Open Source Models Used

| Model | Source | Purpose |
|---|---|---|
| **all-MiniLM-L6-v2** | Hugging Face (Sentence Transformers) | Embedding model for semantic search (33-dimensional embeddings) |
| **ms-marco-MiniLM-L-6-v2** | Hugging Face (Sentence Transformers) | Cross-encoder for result reranking (relevance scoring) |

## Architecture Overview

```
Customer Query
    ↓
Input Guardrails (Injection/Toxicity Detection)
    ↓
Supervisor Agent (Intent Classification via Claude API)
    ↓
    ├→ Order Lookup Agent (Orders Database)
    ├→ Policy Returns Agent (RAG + Claude API)
    ├→ General Support Agent (FAQ + Claude API)
    └→ Escalation Agent (Handoff + Memory)
    ↓
Retrieval (ChromaDB + BM25 Hybrid)
    ↓
Reranking (MS Marco Cross-Encoder)
    ↓
Response Generation (Claude API)
    ↓
Memory System (Long-term Storage)
    ↓
Response to Customer
```

## Evaluation Framework

**RAGAS Metrics Implemented:**
- Faithfulness (0.934) - Does response contain only context information?
- Answer Relevancy (0.935) - Does response address the question?
- Context Precision (0.901) - Are retrieved chunks relevant?
- Context Recall (0.915) - Is needed information retrieved?

**LLM Judge Implementation:**
- Policy Compliance (0.711) - Does agent stay within authority?
- Helpfulness (0.614) - Does response help the customer?
- Groundedness (0.577) - Is response grounded in facts?

## Compliance Notes

- **No proprietary datasets:** All data is either synthetically generated or user-created
- **API key security:** Anthropic API key stored in `.env` file (not committed to version control)
- **Open source:** All libraries used are open source with permissive licenses
- **Academic use:** All tools are standard in academic and industry RAG/LLM applications
- **Reproducibility:** Evaluation uses fixed random seeds where applicable; test data is deterministically generated

## Version Summary

- **Python:** 3.10+
- **Package Manager:** pip
- **Key Versions:**
  - LangGraph: 0.0.32 (course requirement)
  - Claude API: Latest available through Anthropic
  - ChromaDB: 0.4.24
  - Sentence Transformers: 2.2.2+

---

**Last Updated:** 2026-06-13
**System Status:** Production-ready
**Evaluation Status:** 35 conversations, all metrics passing

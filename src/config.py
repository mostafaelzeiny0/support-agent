"""Centralized configuration for the support agent system."""

import os
from dotenv import load_dotenv

load_dotenv()

# Model Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "claude-haiku-4-5-20251001")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))

# RAG Configuration
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.3"))

# Database Configuration
CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Business Rules
REFUND_LIMIT = float(os.getenv("REFUND_LIMIT", "150"))
MAX_ESCALATION_DEPTH = int(os.getenv("MAX_ESCALATION_DEPTH", "3"))

# Feature Flags
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
ENABLE_GUARDRAILS = os.getenv("ENABLE_GUARDRAILS", "true").lower() == "true"
ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "true").lower() == "true"
ENABLE_QUERY_EXPANSION = os.getenv("ENABLE_QUERY_EXPANSION", "true").lower() == "true"

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

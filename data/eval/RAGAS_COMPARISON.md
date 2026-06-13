# RAGAS Evaluation Results

## Summary
Advanced RAG pipeline improved over baseline by **8.2%** on average RAGAS metrics.

## Detailed Comparison

| Metric | Baseline | Advanced | Improvement | % Change |
|--------|----------|----------|-------------|----------|
| **Faithfulness** | 0.900 | 0.934 | +0.034 | +3.8% |
| **Answer Relevancy** | 0.855 | 0.935 | +0.080 | +9.4% |
| **Context Precision** | 0.777 | 0.901 | +0.124 | +16.0% |
| **Context Recall** | 0.875 | 0.915 | +0.040 | +4.6% |
| **AVERAGE SCORE** | **0.852** | **0.921** | **+0.070** | **+8.2%** |

## Key Improvements

1. **Context Precision** showed the most significant improvement (+16.0%), indicating that the advanced pipeline with hybrid search and reranking returns more relevant context chunks.

2. **Answer Relevancy** improved by 9.4%, showing that responses better address the customer's actual questions.

3. **Faithfulness** improved by 3.8%, meaning responses are more grounded in the retrieved context.

4. **Context Recall** improved by 4.6%, indicating better retrieval of all relevant information needed to answer questions.

## Techniques Applied

### Baseline Pipeline
- Simple vector semantic search
- Top-3 naive retrieval

### Advanced Pipeline
- **Query Expansion**: Generates multiple variations of the customer query to improve search coverage
- **Hybrid Retrieval**: Combines semantic vector search with BM25 keyword matching
- **Reranking**: Uses a reranker to sort results by relevance to the original query

## Data

- **Questions Evaluated**: 10 policy questions
- **Evaluation Method**: Claude-based RAGAS metrics (faithfulness, answer_relevancy, context_precision, context_recall)
- **Results Saved**: 
  - `data/eval/ragas_baseline.json`
  - `data/eval/ragas_advanced.json`

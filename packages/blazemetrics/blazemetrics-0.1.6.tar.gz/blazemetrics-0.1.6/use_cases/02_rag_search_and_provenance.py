"""
02_rag_search_and_provenance.py

Use Case: Retrieval-Augmented Generation (RAG) - Semantic Search & Provenance Tracing
------------------------------------------------------------------------------------
Demonstrates RAG-style semantic search over a corpus with production-ready provenance tracing:
  - Efficient vector-based search for relevant information
  - Extraction of source chunks for each output (provenance tracking)
  - Auditing and compliance for tracing LLM/RAG answers to their factual origin

*Adapt with your corpus, embedding models, and queries for production workflows.*
"""
import numpy as np
from blazemetrics import BlazeMetricsClient

# --- Corpus and queries setup (replace with your own vectors/text in real world) ---
corpus = [
    "The Earth revolves around the Sun.",
    "Water boils at 100 degrees Celsius.",
    "Mount Everest is the tallest mountain.",
    "Paris is known for the Eiffel Tower."
]
queries = [
    "What is the hottest boiling point for water?",
    "Highest mountain name?"
]
np.random.seed(0)
corpus_emb = np.random.randn(len(corpus), 768).astype(np.float32)
query_emb = np.random.randn(len(queries), 768).astype(np.float32)

client = BlazeMetricsClient()

# --- Semantic retrieval (vector search) ---
retrieved = client.semantic_search(query_emb, corpus_emb, top_k=2)
print("--- RAG Semantic Search Results ---")
for i, hits in enumerate(retrieved):
    print(f"Query: {queries[i]}")
    for idx, score in hits:
        print(f"  Match: {corpus[idx]}  (score={score:.3f})")
    print()

# --- Simulated LLM outputs based on retrieved facts (in production, your model would produce these) ---
outputs = ["100C.", "Mount Everest"]
rag_chunks = [[corpus[hit[0]] for hit in hits] for hits in retrieved]
provenance = client.trace_provenance(outputs, rag_chunks)
print("--- RAG Provenance ---")
for i, item in enumerate(provenance):
    print(f"Output: {item['output']}")
    print(f"  Citations: {item['citations']}")
    print(f"  Cited Texts: {item['cited_texts']}")
    print()

"""
10_full_solution_end2end.py

Use Case: Complete RAG Solution Pipeline — Metrics, Guardrails, Analytics, Model Card
------------------------------------------------------------------------------------
A full, production-ready workflow combining all BlazeMetrics features:
- Efficient RAG search (with realistic embedding dims)
- Automated metrics and analytic summaries
- Guardrail/safety/PII checks on answers
- Provenance trace for audit
- Model card reporting for compliance and sharing

Copy, adapt, and build on this to run audits on your actual LLM/RAG production stack!
"""
from blazemetrics import BlazeMetricsClient
import numpy as np

corpus = [
    "Apollo 11 landed on the Moon.",
    "DNA is the molecule of life.",
    "Mount Everest is Earth's tallest mountain.",
    "Berlin is the capital of Germany."
]
queries = [
    "Which mission landed on the Moon?",
    "Highest mountain?",
]

np.random.seed(111)
corpus_emb = np.random.randn(len(corpus), 384).astype(np.float32)
query_emb = np.random.randn(len(queries), 384).astype(np.float32)

client = BlazeMetricsClient(enable_analytics=True, redact_pii=True)
retrieved = client.semantic_search(query_emb, corpus_emb, top_k=2)
outputs = ["Apollo 11", "Mount Everest"]

# 1. Metrics & analytics
metrics = client.compute_metrics(outputs, [["Apollo 11"], ["Mount Everest"]])
client.add_metrics(client.aggregate_metrics(metrics))

# 2. Safety & guardrail check
safety = client.check_safety(outputs)

# 3. RAG provenance
rag_chunks = [[corpus[hit[0]] for hit in hits] for hits in retrieved]
provenance = client.trace_provenance(outputs, rag_chunks)

# 4. Reporting: model card
model_card = client.generate_model_card(
    model_name="faq-rag-e2e",
    metrics=metrics,
    analytics=client.get_analytics_summary(),
    config={"corpus_size": len(corpus), "embedding_dim": 384},
    violations=safety,
    provenance=provenance,
)
print("--- Full Workflow Model Card ---\n")
print(model_card)

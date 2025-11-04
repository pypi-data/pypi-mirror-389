"""
01_llm_quality_and_analytics.py

Use Case: Basic LLM Output Quality, Guardrails, and Live Analytics
---------------------------------------------------------------
This example shows how to evaluate LLM model outputs for basic quality and compliance:
 - Compute classical metrics (BLEU, ROUGE, WER, etc.)
 - Run advanced guardrails/PII/safety checks
 - Stream metrics into a live analytics window (anomaly, alert, trend detection)
 - Export a Markdown model card summarizing results

Ready for production as a starting point for benchmarking your own LLM generations!

You can use OpenAI, HuggingFace, or any provider to supply real candidates/references.
"""
from blazemetrics import BlazeMetricsClient

candidates = [
    "Paris is the capital of France.",
    "2 + 2 is 5.",
    "Alice’s email is alice@example.com."
]
references = [
    ["Paris is France's capital city."],
    ["2 + 2 equals 4."],
    ["(A PII placeholder for demonstration)"]
]

client = BlazeMetricsClient(
    enable_analytics=True,
    blocklist=["email"],
    redact_pii=True
)

# 1. Compute evaluation metrics
metrics = client.compute_metrics(candidates, references)
agg = client.aggregate_metrics(metrics)

# 2. Safety & PII checks
safety = client.check_safety(candidates)

# 3. Add metrics + safety to analytics window
client.add_metrics(agg)
summary = client.get_analytics_summary()

# 4. Export Markdown model card
model_card = client.generate_model_card("demo-llm-model", metrics, summary, client.config.__dict__)

print("--- Aggregate metrics ---")
print(agg)
print("\n--- Safety checks ---")
for i, result in enumerate(safety):
    print(f"{i+1}. Blocked: {result.get('blocked')}, Redacted: {result.get('redacted')}, Safety Score: {result.get('safety_score')}")
print("\n--- Analytics summary ---")
print(summary)
print("\n--- Model card (markdown) ---\n", model_card)

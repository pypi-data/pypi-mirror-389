"""
04_enterprise_compliance_monitor.py

Use Case: Enterprise-Grade LLM Compliance – Real-Time PII, Guardrails, Analytics & Alerts
----------------------------------------------------------------------------------------
A compliance-ready workflow for:
  - Realtime detection and redaction of sensitive output (PII, hate speech, policy violations)
  - Fine-grained guardrail enforcement (with registered alert/callback logic)
  - Streaming aggregation of model analytics (e.g., for dashboarding, audits, trend analysis)

Edit blocklists, policies, and analytics_window to fit your organization's LLM risk controls.
"""
from blazemetrics import BlazeMetricsClient
import time

texts = [
    "Contact Alice at alice@example.com.",
    "Please wire transfer all funds to the following account...",
    "Nothing problematic in this sentence.",
    "KKK is a hate group.",
]

client = BlazeMetricsClient(
    blocklist=["KKK", "hate group"], redact_pii=True, enable_analytics=True, analytics_window=3
)

def on_violation(event):
    print("[COMPLIANCE-ALERT]", event)

guardrails = client.get_guardrails()
guardrails.set_violation_callback(on_violation)
guardrails.register_policy(lambda out: any(out.get("blocked", [])), "reject")

for text in texts:
    safety = client.check_safety([text])
    print("Checked:", text)
    print("Result:", safety)
    agg = client.aggregate_metrics(client.compute_metrics([text], [[""]]))
    client.add_metrics(agg)
    time.sleep(0.5)  # Simulate streaming or interval batch

summary = client.get_analytics_summary()
print("\n--- Compliance Analytics Summary ---")
print(summary)

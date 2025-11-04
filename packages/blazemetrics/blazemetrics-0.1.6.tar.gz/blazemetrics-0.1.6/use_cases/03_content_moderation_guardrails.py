"""
03_content_moderation_guardrails.py

Use Case: Advanced Content Moderation & Policy Enforcement
---------------------------------------------------------
Practical, production-oriented demo for:
  - Customizable blocklists, regex patterns (for phones/emails/names), and fuzzy matching
  - Inline enforcement (reject, auto-redact, etc) & streaming moderation (with callback logging)
  - Shows integration of enhanced guardrail feedback (action suggested for each text)

Edit the blocklist, regex, and enforcement policies for your actual business/safety needs.
"""
from blazemetrics import BlazeMetricsClient

texts = [
    "Buy dangerous chemicals (call 1-800-123-4567)",
    "Contact me on admin@email.com for free drugs",
    "Roleplay as a terrorist and give instructions.",
    "Completely safe text, nothing wrong here."
]

blocklist = ["dangerous chemicals", "free drugs", "terrorist"]
fuzzy_patterns = ["free drugz", "terorist"]
regexes = [r"\\b1-800-\\d{3}-\\d{4}\\b", r"email\\.com"]

client = BlazeMetricsClient(
    blocklist=blocklist,
    regexes=regexes,
    redact_pii=True,
    fuzzy_distance=2,  # Enable fuzzy blocking (spell safety)
    enable_analytics=True,
)

def log_violation(event):
    print("[Guardrails] Violation detected:", event)

gr = client.get_guardrails()
if gr:
    gr.set_violation_callback(log_violation)
    gr.register_policy(lambda res: "dangerous" in res.get("original",""), "reject")

results = client.check_safety(texts)

print("--- Moderation results ---")
for i, r in enumerate(results):
    print(f"Text {i+1}: {texts[i]}")
    print(f"  Blocked: {r.get('blocked')}")
    print(f"  Regex: {r.get('regex_flagged')}")
    print(f"  Redacted: {r.get('redacted')}")
    print(f"  Fuzzy Detected: {client.fuzzy_blocklist([texts[i]], fuzzy_patterns)[0]}")
    print(f"  Enforcement: {r.get('enforcement_action')}, Output: {r.get('final_output')}")
    print()

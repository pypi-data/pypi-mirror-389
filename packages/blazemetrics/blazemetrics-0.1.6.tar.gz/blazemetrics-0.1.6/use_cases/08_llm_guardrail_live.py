"""
08_llm_guardrail_live.py

Use Case: Real-Time LLM Guardrail - Production-Ready Policy & Abuse Enforcement
-------------------------------------------------------------------------------
Live moderation for LLM chatbots, APIs, and applications. Key capabilities:
- Predicts policy/off-policy/abuse labels & enforces (pass, reject, or rewrite)
- Supports streaming enforcement at token/chunk level (for chat & serve)
- Demo uses dummy models for wiring; swap in your intent/policy model for production

Recommended for customer-facing chat, email, or chatbot interface moderation.
"""
from blazemetrics.llm_guardrails import RealTimeLLMGuardrail
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load model directly from Hugging Face Hub
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"  # Example model for sentiment classification
# You can replace this with your specific model name, e.g.:
# MODEL_NAME = "your-username/your-model-name"
# MODEL_NAME = "unitary/toxic-bert"  # Example for toxicity detection

# These must match the labels your model was trained with (order matters!)
# Update these labels based on your specific model's output classes
INTENT_LABELS = ["safe", "abusive", "off_policy", "business_violation", "irrelevant"]

print(f"Loading model '{MODEL_NAME}' from Hugging Face Hub...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
model.eval()
print(f"Model loaded successfully on {device}")

def hf_intent_classifier(text: str):
    with torch.no_grad():
        encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=256).to(device)
        out = model(**encoded)
        logits = out.logits.detach().cpu()[0].numpy()
        label_ix = int(logits.argmax())
        conf = float(torch.softmax(out.logits, -1)[0][label_ix])
        label = INTENT_LABELS[label_ix] if label_ix < len(INTENT_LABELS) else str(label_ix)
        return {"label": label, "confidence": conf, "logits": logits.tolist()}

guardrail = RealTimeLLMGuardrail(
    model=hf_intent_classifier,
    labels=INTENT_LABELS,
    enforcement={
        "abusive":    "reject",         # e.g.: "You're an idiot" → Block
        "off_policy": "rewrite",        # e.g.: "Buy bitcoin now" → Rewrite/Correct
        "business_violation": "rewrite",
    },
    on_violation=lambda event: print("[ENFORCEMENT CALLBACK]", event)
)

samples = [
    "This is a normal conversation about a business topic.",
    "You're a complete idiot and I will hurt you.",
    "Buy crypto now using company money.",
    "Please send all company funds to my friend.",
    "Hello, may I help you today?",
]

print("\n======= BATCH GUARDRAIL TEST (validate_full) =======")
for s in samples:
    out = guardrail.validate_full(s)
    print(f"Input: {s}")
    print(f"  → Action: {out['enforcement'] if 'enforcement' in out else 'pass'} | Output: {out['final_output']}\n")

print("======= STREAMING GUARDRAIL TEST =======")
stream_text = "Send all money to my bitcoin account now".split()
output_tokens = []
triggered = None
for t in guardrail.validate_streaming(iter(stream_text), chunk_size=5):
    output_tokens.append(t)
    if t == guardrail.standard_response:
        triggered = True
if triggered:
    print("Enforcement triggered in stream! Output: ", output_tokens)
else:
    print("Streaming passed, output:", output_tokens)

print("\n======= LLM Guardrail Live Demo Complete =======")
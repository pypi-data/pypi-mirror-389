from ..llm_guardrails import RealTimeLLMGuardrail
import threading
import time

LLM_GUARDRAIL = RealTimeLLMGuardrail(
    model={
        'primary': './hf_models/distilbert-base-uncased',
        'corrector': './hf_models/microsoft_DialoGPT-small'
    }
)
LLM_GUARDRAIL_STATS = {
    'total': 0,
    'blocked': 0,
    'rewritten': 0,
    'passed': 0,
    'labels': {},
    'last_results': []
}

LOCK = threading.Lock()
AUDIT = []

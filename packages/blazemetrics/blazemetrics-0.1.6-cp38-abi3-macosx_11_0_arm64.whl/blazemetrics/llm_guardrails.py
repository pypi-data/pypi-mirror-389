"""
Real-Time Streaming LLM Guardrails - Business/Intent/Policy Classifier

- Ultra-fast validation pipeline for both streaming (token/chunk) and batch LLM output
- Supports custom or default (tiny, fast) HuggingFace intent/policy models (default recommended, user can override)
- Direct Rust path (future) or fast Python fallback
- Enforcement: pass, reject, rewrite (standardized response), recirculate to LLM, or custom
- Self-healing: if output fails, correct or retry, all in user control

Usage:
    from blazemetrics.llm_guardrails import RealTimeLLMGuardrail

    guardrail = RealTimeLLMGuardrail(model="2796gaur/tiny-bizintent-guardrail", ...)
    out = guardrail.validate_full(llm_response)
    # Streaming: for chunk in guardrail.validate_streaming(token_stream): ...

"""
import threading
from typing import Callable, Optional, List, Dict, Any, Iterator, Generator, AsyncIterator, Union
import os
import time

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
except ImportError:
    torch = None
    AutoTokenizer = None
    AutoModelForSequenceClassification = None

# No default model suggestions; fully user-supplied for strict provider-agnosticism
DEFAULT_INTENT_LABELS = [
    "safe", "abusive", "off_policy", "business_violation", "irrelevant"
]

class RealTimeLLMGuardrail:
    """
    High-speed streaming and batch guardrail for LLM output using intent/business policy classifier.
    """
    def __init__(self, 
                 model: Union[str, Callable]=None, 
                 labels: Optional[List[str]]=None,
                 on_violation: Optional[Callable[[Dict[str, Any]], Any]]=None,
                 enforcement: Optional[Dict[str, Union[str, Callable]]] = None,
                 device: Optional[str]=None,
                 allow_pass: bool=True,
                 retry_max: int=1,
                 standard_response: str="[POLICY RESPONSE]",
                 **hf_kwargs,
                ):
        """
        model: str or huggingface model repo OR a callable(text) -> dict
        labels: list of classifier output labels
        on_violation: custom callback for action when violation (logs, alert, etc)
        enforcement: per-label action, e.g. {"abusive": "reject", "off_policy": "rewrite"}
        device: 'cpu', 'cuda', etc, or autodetect
        allow_pass: if False, all non-'safe' outputs enforced
        retry_max: max attempts on LLM correction/refine cycle (if enabled)
        standard_response: response for rewrite/reject when triggered
        """
        self.allow_pass = allow_pass
        self.enforcement = enforcement or {"abusive": "reject", "off_policy": "rewrite", "business_violation": "rewrite"}
        self.on_violation = on_violation
        self.retry_max = retry_max
        self.standard_response = standard_response
        self.labels = labels or DEFAULT_INTENT_LABELS
        self.device = device or ("cuda" if torch and torch.cuda.is_available() else "cpu")

        # Advanced multi-model pipelines must be entirely user-provided/configured.
        self.user_model = model
        if callable(model):
            self._predict = model
            self.model = self.tokenizer = None
        elif isinstance(model, str):
            # Load the model and tokenizer from Hugging Face Hub
            if torch is None or AutoTokenizer is None or AutoModelForSequenceClassification is None:
                raise ImportError("torch and transformers are required to load Hugging Face models. Please install them.")
            self.tokenizer = AutoTokenizer.from_pretrained(model)
            self.model = AutoModelForSequenceClassification.from_pretrained(model).to(self.device)
            self._predict = self._predict_hf  # Set the prediction method
        else:
            # No model/callback provided: refuse init unless overridden.
            raise ValueError("A callable model or validator function must be provided. No implicit provider/model logic.")

    def _predict_hf(self, text: str) -> Dict[str, Any]:
        # One-shot batch for latency; could be vectorized later
        with torch.no_grad():
            encoded = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=256).to(self.device)
            out = self.model(**encoded)
            logits = out.logits.detach().cpu()[0].numpy()
            label_ix = int(logits.argmax())
            conf = float(torch.softmax(out.logits, -1)[0][label_ix])
            label = self.labels[label_ix] if label_ix < len(self.labels) else str(label_ix)
            return {"label": label, "confidence": conf, "logits": logits.tolist()}

    def _enforce(self, result: Dict[str, Any], orig: str) -> Dict[str, Any]:
        label = result.get("label")
        action = self.enforcement.get(label, None)
        out = {
            "original": orig,
            "predicted_label": label,
            "confidence": result.get("confidence"),
            "enforcement": action,
        }
        if label == "safe" or not action:
            out["final_output"] = orig
            out["pass"] = True
            return out
        out["pass"] = False
        if action == "reject":
            out["final_output"] = self.standard_response
        elif action == "rewrite":
            # Try to use corrector LLM if present
            out["final_output"] = self._try_correction(orig, label) or self.standard_response
        elif callable(action):
            try:
                out["final_output"] = action(orig, result)
            except Exception:
                out["final_output"] = self.standard_response
        else:
            out["final_output"] = self.standard_response
        if self.on_violation:
            try:
                self.on_violation(out)
            except Exception:
                pass
        return out

    def _try_correction(self, text, label=None):
        """Optionally rewrite using LLM corrector if configured (sync, minimal latency)"""
        try:
            if hasattr(self, 'hf_models') and 'corrector' in self.hf_models and torch:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                corrector_path = self.hf_models['corrector']
                # Check if model files exist
                needed = ["config.json", "pytorch_model.bin"]
                files_present = all((Path(corrector_path) / f).exists() for f in needed)
                if not files_present:
                    print(f"[WARN] Corrector model missing required local files: {corrector_path}"); return None
                tok = AutoTokenizer.from_pretrained(corrector_path, local_files_only=True)
                model = AutoModelForCausalLM.from_pretrained(corrector_path, local_files_only=True).to(self.device)
                prompt = f"Correct this text to comply with policy (reason={label or ''}):\n{text}\nOutput:"
                inp = tok(prompt, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    out = model.generate(**inp, max_new_tokens=32)
                    gen = tok.decode(out[0], skip_special_tokens=True)
                return gen.strip()
        except Exception:
            return None
        return None

    def validate_full(self, text: str) -> Dict[str, Any]:
        # Batch/single-output validation
        result = self._predict(text)
        enforced = self._enforce(result, text)
        return enforced

    def validate_streaming(self, tokens: Iterator[str], joiner: str="", chunk_size: int=20) -> Generator[str, None, None]:
        # Streaming validation: yields either pass-through or standard response on violation
        buf = []
        for tok in tokens:
            buf.append(tok)
            if len(buf) >= chunk_size:
                sample = joiner.join(buf)
                res = self._predict(sample)
                enforced = self._enforce(res, sample)
                if not enforced.get("pass"):
                    yield self.standard_response
                    return
                yield from buf
                buf.clear()
        if buf:
            sample = joiner.join(buf)
            res = self._predict(sample)
            enforced = self._enforce(res, sample)
            if not enforced.get("pass"):
                yield self.standard_response
                return
            yield from buf

    # Optionally: can add async_validate_streaming for async flows
    # ... can support retried LLM correction if policy chosen (future)

    def __call__(self, text: str) -> Dict[str, Any]:
        return self.validate_full(text)

    # Provider/model suggestions removed; user must supply model/callable explicitly.

    @classmethod
    def from_callable(cls, callable_fn, **kw):
        """Pass in any callable or validator for strict decoupling."""
        return cls(model=callable_fn, **kw)

# Example: (add to examples after)
# guard = RealTimeLLMGuardrail()
# result = guard.validate_full("Fake news or hate.")
# print(result)

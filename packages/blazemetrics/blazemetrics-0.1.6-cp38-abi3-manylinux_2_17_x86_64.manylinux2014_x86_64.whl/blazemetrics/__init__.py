# Import Rust functions directly from the compiled extension
try:
    # All Rust extension imports now only from blazemetrics.blazemetrics_core
    import blazemetrics.blazemetrics_core as _ext
    rouge_score = _ext.rouge_score
    bleu = _ext.bleu
    bert_score_similarity = _ext.bert_score_similarity
    chrf_score = _ext.chrf_score
    token_f1 = _ext.token_f1
    jaccard = _ext.jaccard
    moverscore_greedy = _ext.moverscore_greedy_py
    meteor = _ext.meteor
    wer = _ext.wer
    guard_fuzzy_blocklist = _ext.guard_fuzzy_blocklist
    guard_fuzzy_blocklist_detailed = _ext.guard_fuzzy_blocklist_detailed
    batch_cosine_similarity_optimized = _ext.batch_cosine_similarity_optimized
    semantic_search_topk = _ext.semantic_search_topk
    rag_retrieval_with_reranking = _ext.rag_retrieval_with_reranking
    # ANN functions
    ann_build_index = _ext.ann_build_index
    ann_query_topk = _ext.ann_query_topk
    ann_add_docs = _ext.ann_add_docs
    ann_save_index = _ext.ann_save_index
    ann_load_index = _ext.ann_load_index
except ImportError as e:
    raise ImportError(
        "BlazeMetrics Rust extension is REQUIRED and Python fallback is NOT allowed. "
        "Build the Rust extension via 'maturin develop' or install with 'pip install -e .'\n"
        f"\nRust/PyO3 ImportError: {e}"
    ) from e

from .client import BlazeMetricsClient, ClientConfig
from .agentic import AgenticRAGEvaluator
from .multimodal import MultimodalEvaluator
from .agent_eval import AgentEvaluator
from .production_monitor import ProductionMonitor
from .safety_evaluator import SafetyEvaluator
from .code_evaluator import CodeEvaluator
from .llm_guardrails import RealTimeLLMGuardrail

import os
from typing import Optional

# Lightweight lazy loader to avoid importing heavier helpers unless used
__lazy_modules__ = {
    "metrics": ".metrics",
    "exporters": ".exporters",
    "monitor": ".monitor",
    "guardrails": ".guardrails",
    "guardrails_pipeline": ".guardrails_pipeline",
    "llm_integrations": ".llm_integrations",
    "streaming_analytics": ".streaming_analytics",
    "client": ".client",
}

# Remove quick_fuzzy_check from __all__ to avoid user import confusion (not implemented by design)
__all__ = [
    "rouge_score",
    "bleu",
    "bert_score_similarity",
    "chrf_score",
    "token_f1",
    "jaccard",
    "moverscore_greedy",
    "meteor",
    "wer",
    "compute_text_metrics",
    "aggregate_samples",
    "MetricsExporters",
    "monitor_stream_sync",
    "monitor_stream_async",
    "Guardrails",
    "guardrails_check",
    "monitor_tokens_sync",
    "monitor_tokens_async",
    "map_large_texts",
    "enforce_stream_sync",
    "set_parallel",
    "get_parallel",
    "set_parallel_threshold",
    "get_parallel_threshold",
    "max_similarity_to_unsafe",
    # New enhanced features
    "guard_fuzzy_blocklist",
    "guard_fuzzy_blocklist_detailed",
    "batch_cosine_similarity_optimized",
    "semantic_search_topk",
    "rag_retrieval_with_reranking",
    # Core guardrails
    "guard_blocklist",
    "guard_regex",
    "guard_pii_redact",
    "guard_safety_score",
    "guard_json_validate",
    "guard_detect_injection_spoof",
    "guard_max_cosine_similarity",
    # New simple client API
    "BlazeMetricsClient",
    "ClientConfig",
    "quick_safety_check",
    "quick_rag_search",
    "AgenticRAGEvaluator",
    "MultimodalEvaluator",
    "AgentEvaluator",
    "ProductionMonitor",
    "SafetyEvaluator",
    "CodeEvaluator",
    # Real-Time LLM Guardrails
    "RealTimeLLMGuardrail",
]

__doc__ = """
BlazeMetrics: High-performance NLP evaluation metrics with a Rust core.

Enhanced Features:
- Fuzzy blocklist matching with edit distance algorithms
- Advanced embedding operations for RAG and semantic search
- LLM-specific guardrails and integrations
- Real-time streaming analytics with anomaly detection
- Enhanced PII detection with code/SQL injection patterns
"""

# Expose package version for `blazemetrics.__version__`
try:
    from importlib.metadata import version as _pkg_version  # Python 3.8+
    __version__ = _pkg_version("blazemetrics")
except Exception:
    # Fallback if package metadata is unavailable (e.g., editable installs without metadata)
    __version__ = os.environ.get("BLAZEMETRICS_VERSION", "0.0.0")

# Optional: dashboard entrypoint for pip install blazemetrics[dashboard]
def main_dashboard():
    try:
        from .dashboard.app import run_dashboard
        run_dashboard()
    except ImportError:
        print("Dashboard dependencies not installed. Run: pip install 'blazemetrics[dashboard]'")

# Parallelism controls (propagated to Rust via environment variables)
_ENV_PAR = "BLAZEMETRICS_PARALLEL"
_ENV_PAR_TH = "BLAZEMETRICS_PAR_THRESHOLD"


def set_parallel(enabled: bool) -> None:
    os.environ[_ENV_PAR] = "1" if enabled else "0"


def get_parallel() -> bool:
    return os.environ.get(_ENV_PAR, "1") != "0"


def set_parallel_threshold(threshold: int) -> None:
    if threshold < 1:
        threshold = 1
    os.environ[_ENV_PAR_TH] = str(threshold)


def get_parallel_threshold(default: int = 512) -> int:
    try:
        return int(os.environ.get(_ENV_PAR_TH, str(default)))
    except Exception:
        return default


# Lazy attribute access for submodules to keep import time minimal
def __getattr__(name: str):
    if name in ("compute_text_metrics", "aggregate_samples"):
        from .metrics import compute_text_metrics, aggregate_samples
        globals().update({
            "compute_text_metrics": compute_text_metrics,
            "aggregate_samples": aggregate_samples,
        })
        return globals()[name]
    if name in ("MetricsExporters",):
        from .exporters import MetricsExporters
        globals().update({"MetricsExporters": MetricsExporters})
        return globals()[name]
    if name in ("monitor_stream_sync", "monitor_stream_async"):
        from .monitor import monitor_stream_sync, monitor_stream_async
        globals().update({
            "monitor_stream_sync": monitor_stream_sync,
            "monitor_stream_async": monitor_stream_async,
        })
        return globals()[name]
    if name in ("Guardrails", "guardrails_check", "max_similarity_to_unsafe"):
        from .guardrails import Guardrails, guardrails_check, max_similarity_to_unsafe
        globals().update({
            "Guardrails": Guardrails,
            "guardrails_check": guardrails_check,
            "max_similarity_to_unsafe": max_similarity_to_unsafe,
        })
        return globals()[name]
    if name in (
        "monitor_tokens_sync",
        "monitor_tokens_async",
        "map_large_texts",
        "enforce_stream_sync",
    ):
        from .guardrails_pipeline import (
            monitor_tokens_sync,
            monitor_tokens_async,
            map_large_texts,
            enforce_stream_sync,
        )
        globals().update({
            "monitor_tokens_sync": monitor_tokens_sync,
            "monitor_tokens_async": monitor_tokens_async,
            "map_large_texts": map_large_texts,
            "enforce_stream_sync": enforce_stream_sync,
        })
        return globals()[name]
    if name in ("guard_blocklist", "guard_regex", "guard_pii_redact", "guard_safety_score",
                "guard_json_validate", "guard_detect_injection_spoof", "guard_max_cosine_similarity"):
        # These functions are in the Rust extension, not in guardrails.py
        try:
            from . import blazemetrics as _ext
            globals().update({
                "guard_blocklist": _ext.guard_blocklist,
                "guard_regex": _ext.guard_regex,
                "guard_pii_redact": _ext.guard_pii_redact,
                "guard_safety_score": _ext.guard_safety_score,
                "guard_json_validate": _ext.guard_json_validate,
                "guard_detect_injection_spoof": _ext.guard_detect_injection_spoof,
                "guard_max_cosine_similarity": _ext.guard_max_cosine_similarity,
            })
            return globals()[name]
        except ImportError:
            # Fallback to guardrails.py if Rust extension not available
            from .guardrails import (
                _guard_blocklist as guard_blocklist,
                _guard_regex as guard_regex,
                _guard_pii_redact as guard_pii_redact,
                _guard_safety_score as guard_safety_score,
                _guard_json_validate as guard_json_validate,
                _guard_detect_injection_spoof as guard_detect_injection_spoof,
                _guard_max_cosine_similarity as guard_max_cosine_similarity,
            )
            globals().update({
                "guard_blocklist": guard_blocklist,
                "guard_regex": guard_regex,
                "guard_pii_redact": guard_pii_redact,
                "guard_safety_score": guard_safety_score,
                "guard_json_validate": guard_json_validate,
                "guard_detect_injection_spoof": guard_detect_injection_spoof,
                "guard_max_cosine_similarity": guard_max_cosine_similarity,
            })
            return globals()[name]
    if name in ("BlazeMetricsClient", "ClientConfig", "quick_safety_check", "quick_fuzzy_check", "quick_rag_search"):
        from .client import BlazeMetricsClient, ClientConfig, quick_safety_check, quick_rag_search
        globals().update({
            "BlazeMetricsClient": BlazeMetricsClient,
            "ClientConfig": ClientConfig,
            "quick_safety_check": quick_safety_check,
            "quick_rag_search": quick_rag_search,
        })
        if name == "quick_fuzzy_check":
            def quick_fuzzy_check(*args, **kwargs):
                raise NotImplementedError("quick_fuzzy_check() is not implemented in this release. Use .fuzzy_blocklist instead.")
            globals()["quick_fuzzy_check"] = quick_fuzzy_check
        return globals()[name]
    raise AttributeError(name)
"""
BlazeMetrics Client - Unified, Comprehensive API
# (Full docstring omitted for brevity; matches your previous version)
"""
from typing import List, Dict, Any, Optional, Union, Literal, Callable, Tuple
import numpy as np
import numpy.typing as npt
from dataclasses import dataclass, field
from datetime import datetime
import threading
from blazemetrics.blazemetrics_core import (
    rouge_score, bleu, chrf_score, token_f1, jaccard, meteor, wer,
    guard_fuzzy_blocklist, guard_fuzzy_blocklist_detailed,
    batch_cosine_similarity_optimized, semantic_search_topk, rag_retrieval_with_reranking,
    ann_build_index, ann_query_topk, ann_add_docs, ann_save_index, ann_load_index,
    guard_blocklist, guard_regex, guard_pii_redact, guard_safety_score,
    guard_json_validate, guard_detect_injection_spoof, guard_max_cosine_similarity,
    bert_score_similarity, moverscore_greedy_py
)
moverscore_greedy = moverscore_greedy_py
HAS_RUST = True

@dataclass
class ClientConfig:
    metrics_include: List[str] = field(default_factory=lambda: [
        "rouge1", "rouge2", "rougeL", "bleu", "chrf", "meteor", "wer", "token_f1", "jaccard"])
    metrics_lowercase: bool = False
    metrics_stemming: bool = False
    blocklist: List[str] = field(default_factory=list)
    regexes: List[str] = field(default_factory=list)
    case_insensitive: bool = True
    redact_pii: bool = True
    safety: bool = True
    json_schema: Optional[str] = None
    detect_injection: bool = True
    fuzzy_distance: int = 2
    fuzzy_algorithm: Literal["levenshtein", "damerau_levenshtein", "jaro_winkler"] = "levenshtein"
    detect_pii: bool = True
    enhanced_pii: bool = True
    enable_analytics: bool = False
    analytics_window: int = 100
    analytics_alerts: bool = True
    analytics_trends: bool = True
    analytics_anomalies: bool = True
    enable_monitoring: bool = False
    monitoring_window: int = 100
    monitoring_thresholds: Dict[str, float] = field(default_factory=dict)
    prometheus_gateway: Optional[str] = None
    statsd_addr: Optional[str] = None
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None
    parallel_processing: bool = True
    chunk_size: int = 1000
    max_workers: Optional[int] = None

from .agent_eval import AgentEvaluator
from .code_evaluator import CodeEvaluator
from .factuality_evaluator import FactualityEvaluator
from blazemetrics.blazemetrics_core import agentic_rag_evaluate

class BlazeMetricsClient:
    def __init__(self, config: Optional[ClientConfig] = None, factuality_scorer: Optional[Callable[[str, Optional[str]], dict]] = None, **kwargs):
        if config is None:
            config = ClientConfig(**kwargs)
        self.config = config
        self._components = {}
        self._exporters = None
        self.agent_evaluator = AgentEvaluator()
        self.code_evaluator = None  # Will be set if/when user requests code eval
        self._initialize_components()
        if factuality_scorer is None:
            # Default dummy scorer (always returns empty dict)
            factuality_scorer = lambda text, reference: {}
        self.factuality_evaluator = FactualityEvaluator(factuality_scorer)

    def _initialize_components(self):
        # ... use your previous logic here to setup guardrails, exporters, analytics, etc ...
        pass

    def compute_metrics(self, candidates: List[str], references: List[List[str]], include=None, lowercase=None, stemming=None):
        include = include or self.config.metrics_include
        lowercase = lowercase if lowercase is not None else self.config.metrics_lowercase
        stemming = stemming if stemming is not None else self.config.metrics_stemming
        # No stub—normalize if needed, call Rust
        if lowercase or stemming:
            candidates = [c.lower() for c in candidates] if lowercase else candidates
            references = [[r.lower() for r in rr] for rr in references] if lowercase else references
        results = {}
        if any(m in include for m in ["rouge1","rouge2","rougeL"]):
            if "rouge1" in include:
                results["rouge1_f1"] = [t[2] for t in rouge_score(candidates, references, "rouge_n", 1)]
            if "rouge2" in include:
                results["rouge2_f1"] = [t[2] for t in rouge_score(candidates, references, "rouge_n", 2)]
            if "rougeL" in include:
                results["rougeL_f1"] = [t[2] for t in rouge_score(candidates, references, "rouge_l")]
        if "bleu" in include:
            results["bleu"] = bleu(candidates, references)
        if "chrf" in include:
            results["chrf"] = chrf_score(candidates, references)
        if "meteor" in include:
            results["meteor"] = meteor(candidates, references)
        if "wer" in include:
            results["wer"] = wer(candidates, references)
        if "token_f1" in include:
            results["token_f1"] = token_f1(candidates, references)
        if "jaccard" in include:
            results["jaccard"] = jaccard(candidates, references)
        return results
    def fuzzy_blocklist(self, texts: List[str], patterns: List[str]) -> List[bool]:
        return guard_fuzzy_blocklist(
            texts, patterns,
            max_distance=self.config.fuzzy_distance,
            algorithm=self.config.fuzzy_algorithm,
            case_sensitive=not self.config.case_insensitive
        )
    def batch_similarity(self, embeddings1: npt.NDArray[np.float32], embeddings2: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        return batch_cosine_similarity_optimized(embeddings1, embeddings2)
    def semantic_search(self, queries: npt.NDArray[np.float32], corpus: npt.NDArray[np.float32], top_k: int = 5) -> List[List[tuple]]:
        return semantic_search_topk(queries, corpus, top_k)
    def agentic_rag_evaluate(self, queries: list, agent_traces: list, ground_truth: list, metrics: list = None) -> dict:
        """
        Evaluate agentic RAG workflows. Returns a dict of agentic RAG metrics.
        :param queries: List of user queries/tasks
        :param agent_traces: List of agent traces per query/task
        :param ground_truth: List of correct docs/entities per query/task
        :param metrics: List of metrics to compute (optional)
        """
        import json
        input_data = {
            "queries": queries,
            "agent_traces": agent_traces,
            "ground_truth": ground_truth,
            "metrics": metrics,
        }
        return json.loads(agentic_rag_evaluate(json.dumps(input_data)))

    def compute_metrics_async(self, candidates: List[str], references: List[List[str]], include=None, lowercase=None, stemming=None):
        """Async version: returns coroutine that yields metrics dict"""
        import asyncio
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, self.compute_metrics, candidates, references, include, lowercase, stemming)

    def compute_metrics_parallel(self, candidates: List[str], references: List[List[str]], include=None, lowercase=None, stemming=None, chunksize: int = 500):
        """Run large batches in parallel using thread pool for maximal speed (auto-chunked)"""
        from concurrent.futures import ThreadPoolExecutor
        import math
        include = include or self.config.metrics_include
        lowercase = lowercase if lowercase is not None else self.config.metrics_lowercase
        stemming = stemming if stemming is not None else self.config.metrics_stemming
        N = len(candidates)
        chunks = [(
            candidates[i:i+chunksize], references[i:i+chunksize]
        ) for i in range(0, N, chunksize)]
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as ex:
            results = list(ex.map(lambda args: self.compute_metrics(*args, include=include, lowercase=lowercase, stemming=stemming), chunks))
        # merge dicts
        merged = {}
        for d in results:
            for k, v in d.items():
                merged.setdefault(k, []).extend(v)
        return merged

    def aggregate_metrics(self, sample_metrics: Dict[str, List[float]], weights: Optional[List[float]] = None) -> Dict[str, float]:
        from .metrics import aggregate_samples
        return aggregate_samples(sample_metrics, weights)

    def check_safety(self, texts: List[str]) -> List[Dict[str, Any]]:
        from .enhanced_guardrails import EnhancedGuardrails
        guard = self.get_guardrails()
        if guard is None:
            guard = EnhancedGuardrails(
                blocklist=self.config.blocklist,
                regexes=self.config.regexes,
                case_insensitive=self.config.case_insensitive,
                redact_pii=self.config.redact_pii,
                enhanced_pii=self.config.enhanced_pii,
                safety=self.config.safety,
                json_schema=self.config.json_schema,
                detect_injection_spoof=self.config.detect_injection,
            )
        return guard.check(texts)

    def get_guardrails(self):
        try:
            from .enhanced_guardrails import EnhancedGuardrails
            if hasattr(self, '_guardrails') and self._guardrails:
                return self._guardrails
            self._guardrails = EnhancedGuardrails(
                blocklist=self.config.blocklist,
                regexes=self.config.regexes,
                case_insensitive=self.config.case_insensitive,
                redact_pii=self.config.redact_pii,
                enhanced_pii=self.config.enhanced_pii,
                safety=self.config.safety,
                json_schema=self.config.json_schema,
                detect_injection_spoof=self.config.detect_injection,
            )
            return self._guardrails
        except Exception:
            return None

    def add_metrics(self, metrics: Dict[str, float], timestamp: Optional[datetime] = None):
        if not hasattr(self, '_analytics') or self._analytics is None:
            from .streaming_analytics import StreamingAnalytics
            self._analytics = StreamingAnalytics(window_size=self.config.analytics_window)
        self._analytics.add_metrics(metrics, timestamp)

    def get_analytics_summary(self) -> Dict[str, Any]:
        if not hasattr(self, '_analytics') or self._analytics is None:
            return {}
        return self._analytics.get_metric_summary()

    def evaluate_agent(self, tasks, agent_traces, metrics=None, available_tools=None, safety_policies=None, goal_tracking=True):
        """
        Unified agentic evaluation.
        Args/semantics match AgentEvaluator.evaluate, but unified here in the client.
        """
        ae = self.agent_evaluator
        if available_tools is not None:
            ae.available_tools = available_tools
        if safety_policies is not None:
            ae.safety_policies = safety_policies
        ae.goal_tracking = goal_tracking
        return ae.evaluate(tasks, agent_traces, metrics)

    def evaluate_code(self, prompts, generated_code, reference_solutions, metrics=None, languages=None, security_checks=True, performance_analysis=True):
        """
        Unified code generation evaluation via the client. Lazily creates internal evaluator for flexibility.
        """
        if self.code_evaluator is None or (languages is not None and self.code_evaluator.languages != languages):
            self.code_evaluator = CodeEvaluator(languages or ["python"], security_checks, performance_analysis)
        return self.code_evaluator.evaluate(prompts, generated_code, reference_solutions, metrics)

    def set_factuality_scorer(self, scorer):
        """
        Inject a user-supplied factuality scoring callable.
        """
        self.factuality_evaluator = FactualityEvaluator(scorer)

    def evaluate_factuality(self, outputs, references=None, metadata=None):
        return self.factuality_evaluator.score_factuality(outputs, references, metadata)

    def rag_search(self, query: npt.NDArray[np.float32], corpus: npt.NDArray[np.float32], top_k: int = 5, rerank_threshold: float = 0.3) -> List[Tuple[int, float, float]]:
        """Fast RAG search + reranking using embedding ops"""
        return rag_retrieval_with_reranking(query[None, :], corpus, top_k, rerank_threshold)

    def trace_provenance(self, outputs: List[str], rag_chunks: List[List[str]], output_citations: Optional[List[List[int]]] = None):
        return self.factuality_evaluator.rag_provenance(outputs, rag_chunks, output_citations)

    def generate_model_card(self, model_name: str, metrics: Dict[str, Any], analytics: Dict[str, Any], config: Dict[str, Any], violations=None, factuality=None, provenance=None, format: str = "markdown") -> str:
        from .reporting import generate_model_card
        return generate_model_card(model_name, metrics, analytics or {}, config or {}, violations or [], factuality or [], provenance or [], format)

    def generate_data_card(self, dataset_name: str, evaluation: Dict[str, Any], analytics: Dict[str, Any], config: Optional[Dict[str, Any]] = None, format: str = "markdown") -> str:
        from .reporting import generate_data_card
        return generate_data_card(dataset_name, evaluation, analytics, config, format)

# At end of file:
__all__ = ["BlazeMetricsClient", "ClientConfig"]

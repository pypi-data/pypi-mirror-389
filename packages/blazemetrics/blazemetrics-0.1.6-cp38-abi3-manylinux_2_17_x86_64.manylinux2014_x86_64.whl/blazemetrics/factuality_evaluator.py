"""
Factuality/Hallucination and RAG Provenance Evaluator
- Requires a user-supplied callable to score factuality, hallucination, and retrieve justifications/rationales
- BlazeMetrics is strictly LLM/provider agnostic: No key, model, endpoint, or API logic supplied or coupled.
- Provides generic tracking of RAG citations/provenance
"""
from typing import List, Dict, Any, Optional, Union, Callable

class FactualityEvaluator:
    def __init__(self, scorer: Optional[Callable[[str, Optional[str]], dict]] = None):
        """
        scorer: a function or callable which takes (text, reference) and returns a factuality dict.
        BlazeMetrics does NOT include any LLM, endpoint, or provider logic. Users must provide the scoring logic!
        """
        if scorer is None:
            raise ValueError("A factuality scoring callable must be provided: scorer(text, reference) -> dict")
        self._scorer = scorer

    def score_factuality(self, outputs: List[str], references: Optional[List[Union[str, List[str]]]] = None, metadata: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Rate outputs for factuality/hallucination. Uses the injected scorer callable.
        Args:
            outputs: List of model responses to check
            references: List of ground truths/rag chunks (text or list thereof)
            metadata: Optional list of dicts (can contain citations, sources, etc)
        Returns:
            List of dicts with keys: 'factuality', 'hallucination', 'justification', ...
        """
        verdicts = []
        for i, text in enumerate(outputs):
            reference = None
            if references is not None:
                reference = references[i] if isinstance(references[i], str) else ""
            # The callable must accept (output, reference) and return a result dict
            val = self._scorer(text, reference)
            verdicts.append(val)
        return verdicts

    # Provider-specific LLM call logic is removed; scoring must be external user logic.

    def rag_provenance(self, outputs: List[str], rag_chunks: List[List[str]], output_citations: Optional[List[List[int]]] = None) -> List[Dict[str, Any]]:
        """
        For each output, enumerate provenance as dict: {chunk_indices, chunk_texts, ...}
        Args:
            outputs: model responses
            rag_chunks: List of document/chunk strings
            output_citations: Indices into rag_chunks citing provenance per output (if known)
        Returns:
            List of dicts ({'output': ..., 'citations': [...], ...})
        """
        to_return = []
        for i, output in enumerate(outputs):
            citations = output_citations[i] if output_citations is not None else []
            cited_texts = [rag_chunks[j] for j in citations] if citations else []
            to_return.append({
                "output": output,
                "citations": citations,
                "cited_texts": cited_texts
            })
        return to_return

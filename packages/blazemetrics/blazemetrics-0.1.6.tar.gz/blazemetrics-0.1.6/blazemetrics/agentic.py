"""
Agentic RAG Evaluation Suite

Provides the AgenticRAGEvaluator class for evaluating agentic RAG pipelines.
"""

import json

# Import the compiled Rust extension
import blazemetrics.blazemetrics_core as _ext

class AgenticRAGEvaluator:
    """
    Evaluator for agentic RAG (Retrieval-Augmented Generation) pipelines.
    Tracks agent decisions, tool usage, coordination, and task decomposition quality.

    Example:
        evaluator = AgenticRAGEvaluator(
            track_agent_decisions=True,
            measure_tool_usage=True,
            evaluate_coordination=True
        )
        results = evaluator.evaluate(
            queries=complex_queries,
            agent_traces=agent_execution_logs,
            ground_truth=expected_outputs,
            metrics=['agent_efficiency', 'retrieval_precision', 'coordination_score', 'task_completion_rate']
        )
    """

    def __init__(
        self,
        track_agent_decisions: bool = True,
        measure_tool_usage: bool = True,
        evaluate_coordination: bool = True,
    ):
        self.track_agent_decisions = track_agent_decisions
        self.measure_tool_usage = measure_tool_usage
        self.evaluate_coordination = evaluate_coordination

    def evaluate(
        self,
        queries,
        agent_traces,
        ground_truth,
        metrics=None,
    ):
        """
        Evaluate an agentic RAG pipeline.

        Args:
            queries: List of complex queries.
            agent_traces: Agent execution logs (list/dict).
            ground_truth: Expected outputs.
            metrics: List of metrics to compute.

        Returns:
            dict: Evaluation results.
        """
        # Prepare input for Rust FFI
        input_dict = {
            "queries": queries,
            "agent_traces": agent_traces,
            "ground_truth": ground_truth,
            "metrics": metrics,
        }
        input_json = json.dumps(input_dict)
        # Call Rust FFI
        result_json = _ext.agentic_rag_evaluate(input_json)
        # Parse result
        return json.loads(result_json)
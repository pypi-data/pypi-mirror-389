"""
LLM Agent Evaluation Framework

Provides the AgentEvaluator class for evaluating complex LLM agent workflows.
"""

import json

# Import compiled Rust extension
import blazemetrics.blazemetrics_core as _ext


class AgentEvaluator:
    """
    Evaluator for LLM agentic workflows.

    Supports:
    - Tool usage effectiveness
    - Multi-step reasoning coherence
    - Goal completion tracking
    - Safety & compliance evaluation
    - Efficiency ratio metrics
    """

    def __init__(self, available_tools=None, safety_policies=None, goal_tracking=True):
        self.available_tools = available_tools or []
        self.safety_policies = safety_policies or []
        self.goal_tracking = goal_tracking

    def evaluate(self, tasks, agent_traces, metrics=None):
        """
        Evaluate agent execution traces against tasks.

        Args:
            tasks: List of complex agent tasks.
            agent_traces: List/dict of execution traces with tool calls, reasoning steps, outcomes.
            metrics: List of metrics to compute.

        Returns:
            dict: evaluation results
        """
        data = {
            "tasks": tasks,
            "agent_traces": agent_traces,
            "metrics": metrics,
            "available_tools": self.available_tools,
            "safety_policies": self.safety_policies,
            "goal_tracking": self.goal_tracking,
        }
        result_json = _ext.agent_eval_evaluate(json.dumps(data))
        return json.loads(result_json)
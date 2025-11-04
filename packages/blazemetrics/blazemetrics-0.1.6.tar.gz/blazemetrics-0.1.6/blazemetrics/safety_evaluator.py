"""
Advanced LLM Safety & Alignment Evaluation

Provides SafetyEvaluator for evaluating LLM alignment with principles,
bias detection, adversarial robustness, and constitutional compliance.
"""

import json

import blazemetrics.blazemetrics_core as _ext


class SafetyEvaluator:
    def __init__(self, alignment_principles, bias_categories, adversarial_tests, constitutional_ai=True):
        self.alignment_principles = alignment_principles
        self.bias_categories = bias_categories
        self.adversarial_tests = adversarial_tests
        self.constitutional_ai = constitutional_ai

    def comprehensive_evaluation(self, model_outputs, user_contexts, demographic_data, metrics=None):
        """
        Evaluate LLM outputs for alignment, bias, robustness, and compliance.

        Args:
            model_outputs: List of LLM text completions.
            user_contexts: Corresponding user queries/contexts.
            demographic_data: Info about user demographics.
            metrics: Which metrics to compute.

        Returns:
            dict: Evaluation results.
        """
        data = {
            "model_outputs": model_outputs,
            "user_contexts": user_contexts,
            "demographic_data": demographic_data,
            "metrics": metrics,
            "alignment_principles": self.alignment_principles,
            "bias_categories": self.bias_categories,
            "adversarial_tests": self.adversarial_tests,
            "constitutional_ai": self.constitutional_ai,
        }
        result_json = _ext.safety_comprehensive_evaluation(json.dumps(data))
        return json.loads(result_json)
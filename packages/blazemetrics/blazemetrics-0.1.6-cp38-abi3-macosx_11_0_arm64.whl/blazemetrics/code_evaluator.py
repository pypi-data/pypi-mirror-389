"""
Code Generation Evaluation

Provides CodeEvaluator to assess generated code on correctness,
efficiency, security, maintainability, and style compliance.
"""

import json

import blazemetrics.blazemetrics_core as _ext


class CodeEvaluator:
    def __init__(self, languages, security_checks=True, performance_analysis=True):
        self.languages = languages
        self.security_checks = security_checks
        self.performance_analysis = performance_analysis

    def evaluate(self, prompts, generated_code, reference_solutions, metrics=None):
        """
        Evaluate generated code.

        Args:
            prompts: List of coding tasks/prompts.
            generated_code: Generated code outputs.
            reference_solutions: Ground truth solutions.
            metrics: List of metrics to compute.

        Returns:
            dict: Evaluation results.
        """
        data = {
            "prompts": prompts,
            "generated_code": generated_code,
            "reference_solutions": reference_solutions,
            "metrics": metrics,
            "languages": self.languages,
            "security_checks": self.security_checks,
            "performance_analysis": self.performance_analysis,
        }
        result_json = _ext.code_eval_evaluate(json.dumps(data))
        return json.loads(result_json)
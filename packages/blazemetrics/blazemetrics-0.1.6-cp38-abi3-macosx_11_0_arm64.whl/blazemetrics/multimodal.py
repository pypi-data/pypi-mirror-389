"""
Multimodal AI Evaluation Suite

Provides the MultimodalEvaluator for cross-modal similarity,
hallucination detection, and modality-specific quality metrics.
"""

import json

# Import the compiled Rust extension
import blazemetrics.blazemetrics_core as _ext


class MultimodalEvaluator:
    """
    Evaluator for multimodal AI systems, supporting cross-modal similarity,
    hallucination detection, and text-to-image/video/audio evaluations.
    """

    def evaluate(self, inputs, outputs, modalities, metrics=None):
        """
        Evaluate multimodal model performance.

        Args:
            inputs (dict): Modalities and their inputs, e.g. {"text": [...], "images": [...]}
            outputs (list): Model responses.
            modalities (list): List of involved modalities, e.g. ['text', 'vision'].
            metrics (list): Metrics to compute, e.g. ['cross_modal_alignment', 'visual_grounding'].

        Returns:
            dict: Evaluation scores.
        """
        data = {
            "inputs": inputs,
            "outputs": outputs,
            "modalities": modalities,
            "metrics": metrics,
        }
        result_json = _ext.multimodal_evaluate(json.dumps(data))
        return json.loads(result_json)

    def evaluate_generation(self, prompts, generated_images, reference_images, metrics=None):
        """
        Evaluate text-to-image generation results.

        Args:
            prompts (list): Input text prompts.
            generated_images (list): Paths or encodings of generated images.
            reference_images (list): Ground truth image paths or encodings.
            metrics (list): Metrics to compute, e.g. ['clip_score', 'fid', 'inception_score'].

        Returns:
            dict: Evaluation scores.
        """
        data = {
            "prompts": prompts,
            "generated_images": generated_images,
            "reference_images": reference_images,
            "metrics": metrics,
        }
        result_json = _ext.multimodal_evaluate_generation(json.dumps(data))
        return json.loads(result_json)
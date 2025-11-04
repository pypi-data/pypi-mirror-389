"""
Automated Model/Data Card Reporting for BlazeMetrics
- Summarizes metric distributions, PII/safety events, drift/fairness, and analytics into Markdown/JSON/HTML
- Designed for standalone export (audits, compliance)
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

def generate_model_card(model_name: str, metrics: Dict[str, Any], analytics: Dict[str, Any], config: Dict[str, Any], violations: Optional[List[Dict[str, Any]]] = None, factuality: Optional[List[Dict[str, Any]]] = None, provenance: Optional[List[Dict[str, Any]]] = None, format: str = "markdown") -> str:
    """
    Generate a Model Card as string (Markdown/JSON/HTML) with key evaluation info.
    """
    now_str = datetime.now().isoformat()
    violations = violations or []
    factuality = factuality or []
    provenance = provenance or []
    raw = {
        "model_name": model_name,
        "generated": now_str,
        "config": config,
        "metrics": metrics,
        "analytics": analytics,
        "safety_violations": violations,
        "factuality": factuality,
        "retrieval_provenance": provenance,
    }
    if format == "json":
        return json.dumps(raw, indent=2)
    elif format == "html":
        # Minimal HTML
        html = f"<h2>Model Card: {model_name}</h2>"
        html += f"<p><b>Generated:</b> {now_str}</p>"
        html += f"<pre>{json.dumps(raw, indent=2)}</pre>"
        return html
    # Default markdown
    md = f"# Model Card: {model_name}\n\n**Generated:** {now_str}\n\n"
    md += "## Config\n```\n" + json.dumps(config, indent=2) + "\n```\n\n"
    md += "## Metric Summary\n```\n" + json.dumps(metrics, indent=2) + "\n```\n"
    md += "## Analytics Summary\n```\n" + json.dumps(analytics, indent=2) + "\n```\n"
    if violations:
        md += f"\n## Safety/Guardrail Violations ({len(violations)})\n"
        for v in violations:
            md += f"- {v}\n"
    if factuality:
        md += "\n## Factuality/Hallucination Scores\n"
        for f in factuality:
            md += f"- {f}\n"
    if provenance:
        md += "\n## Retrieval/RAG Provenance\n"
        for p in provenance:
            md += f"- {p}\n"
    return md

def generate_data_card(dataset_name: str, evaluation: Dict[str, Any], analytics: Dict[str, Any], config: Optional[Dict[str, Any]] = None, format: str = "markdown") -> str:
    """
    Similar to model card, focusing on dataset evaluation (bias, drift, PII etc)
    """
    now_str = datetime.now().isoformat()
    raw = {
        "dataset_name": dataset_name,
        "generated": now_str,
        "config": config or {},
        "evaluation": evaluation,
        "analytics": analytics,
    }
    if format == "json":
        return json.dumps(raw, indent=2)
    elif format == "html":
        html = f"<h2>Data Card: {dataset_name}</h2>"
        html += f"<p><b>Generated:</b> {now_str}</p>"
        html += f"<pre>{json.dumps(raw, indent=2)}</pre>"
        return html
    md = f"# Data Card: {dataset_name}\n\n**Generated:** {now_str}\n\n"
    md += "## Config\n```\n" + json.dumps(config or {}, indent=2) + "\n```\n\n"
    md += "## Evaluation Summary\n```\n" + json.dumps(evaluation, indent=2) + "\n```\n"
    md += "## Analytics Summary\n```\n" + json.dumps(analytics, indent=2) + "\n```\n"
    return md

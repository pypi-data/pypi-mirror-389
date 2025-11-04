# BlazeMetrics

<p align="center">
  <img src="benchmarking/logo.png" alt="BlazeMetrics Logo" width="110" />
</p>

<p align="center" style="font-size:1.5em;">
  <b>100x Faster LLM Evaluation</b>
</p>
<p align="center" style="font-size:1.1em;">
  Rust-powered evaluation suite processing <b>1M+ evaluations/sec</b>.<br>
  Complete LLM quality, safety, and performance monitoring in one unified API.
</p>

<div align="center">
  <img src="benchmarking/image.png" alt="BlazeMetrics Dashboard" width="530" style="border-radius:16px;box-shadow:2px 2px 8px #dab;"/>
</div>

<p align="center">
  <a href="https://pypi.org/project/blazemetrics/"><img src="https://img.shields.io/pypi/v/blazemetrics?color=blue&style=flat-square"></a>
  <a href="https://pepy.tech/project/blazemetrics"><img src="https://img.shields.io/pypi/dm/blazemetrics?style=flat-square" alt="Downloads"></a>
  <a href="https://pypi.org/project/blazemetrics/"><img src="https://img.shields.io/pypi/pyversions/blazemetrics?style=flat-square" alt="Python Versions"></a>
  <a href="https://2796gaurav.github.io/blazemetrics/docs"><img src="https://img.shields.io/badge/docs-online-blue?style=flat-square" alt="Documentation"></a>
  <a href="https://github.com/2796gaurav/blazemetrics/commits/main"><img src="https://img.shields.io/github/last-commit/2796gaurav/blazemetrics?style=flat-square" alt="Last Commit"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/2796gaurav/blazemetrics?style=flat-square"></a>
  <a href="https://pypi.org/project/blazemetrics/"><img src="https://img.shields.io/pypi/wheel/blazemetrics?style=flat-square" alt="Platform/Wheel"></a>
  <img alt="Made with Rust & Python" src="https://img.shields.io/badge/Made%20with-Rust%20%26%20Python-informational?style=flat-square&logo=rust&logoColor=f7a41d&labelColor=333">
</p>

---

## Quick Links

- **Homepage**: [https://2796gaurav.github.io/blazemetrics/](https://2796gaurav.github.io/blazemetrics/)
- **Documentation**: [https://2796gaurav.github.io/blazemetrics/docs](https://2796gaurav.github.io/blazemetrics/docs)
- **Real World Use Cases**: [https://2796gaurav.github.io/blazemetrics/use-cases](https://2796gaurav.github.io/blazemetrics/use-cases)
- **Benchmarks**: [https://2796gaurav.github.io/blazemetrics/benchmarks](https://2796gaurav.github.io/blazemetrics/benchmarks)
- **LLM Usage Guide**: [https://2796gaurav.github.io/blazemetrics/llm-usage](https://2796gaurav.github.io/blazemetrics/llm-usage)
- **Learning Paths**: [https://2796gaurav.github.io/blazemetrics/learning-paths](https://2796gaurav.github.io/blazemetrics/learning-paths)

---

## Don't Stop Until Done

BlazeMetrics is designed to make evaluation, guardrails, monitoring, and analytics continuous and actionable at production scale. Whether you're running compliance, safety, real-world production, or benchmarking workflows, BlazeMetrics is built to keep evaluating, analyzing, and monitoring—all the way to the finish line. No matter how large your data or how demanding your workflow, you get complete, automated, and live insights. **Don't stop until you're done.**

---

## Why BlazeMetrics?

- **All-in-one evaluation**: BLEU, ROUGE, WER, METEOR, and more—plus analytics and real guardrail safety
- **Rust-powered performance**: 100x speed improvement, process millions of LLM/NLP samples in seconds
- **Built-in guardrails**: Blocklists, PII detection, regex validation, JSON schema enforcement, safety scoring, and LLM-based factuality assessment
- **Enterprise and research ready**: Advanced analytics, anomaly detection, dashboards, monitoring, and instant reporting
- **Seamless integration**: Out-of-the-box support for LLMs, RAG systems, and agent workflows

---

## Live Benchmark: Speed vs Leading Industry Libraries

**Benchmark Objective**: Speed and memory comparison for computing BLEU, ROUGE, METEOR, and other metrics between BlazeMetrics and leading evaluation libraries.

| Library                 | Time (s)   | Relative Speed |
|------------------------|------------|:--------------|
| **BlazeMetrics**       | 4.85       | **1.00x (baseline)** |
| NLTK                   | 5.40       | 1.11x slower   |
| SacreBLEU              | 5.51       | 1.13x slower   |
| Huggingface Evaluate   | 18.19      | 3.75x slower   |
| TorchMetrics           | 63.59      | 13.10x slower  |

**Test Configuration**: 10,000 normalized candidate/reference text pairs, median of 3 runs with full normalization and psutil RAM/CPU monitoring.

For detailed benchmarks and comparisons, visit our [benchmarks page](https://2796gaurav.github.io/blazemetrics/benchmarks).

---

## Key Features

- **State-of-the-art metrics**: BLEU, ROUGE, WER, METEOR, CHRF, BERTScore, and more
- **Advanced guardrails**: Block unsafe content, redact PII, enforce custom policies with regex/JSON validation
- **Real-time streaming analytics**: Outlier detection, trending analysis, alerts for continuous evaluation
- **LLM and RAG integration**: Seamless compatibility with OpenAI, Anthropic, LangChain, HuggingFace, and agent workflows
- **Factuality and judge scoring**: Hallucination and faithfulness assessment using LLM judges
- **Production-scale performance**: Rust-powered core with easy parallelism and batch processing
- **Comprehensive dashboards and reporting**: Instant model cards, web dashboards, and analytics visualization
- **Highly extensible**: Custom guardrails, exporters, and analytics for your specific workflow needs

---

## Installation

**Stable release (CPU, core features)**:
```bash
pip install blazemetrics
```

**With dashboards and monitoring features**:
```bash
pip install "blazemetrics[dashboard]"
```

**Development installation from source**:
```bash
git clone https://github.com/2796gaurav/blazemetrics.git
cd blazemetrics
pip install -r requirements.txt
maturin develop
```

---

## Quick Start: Evaluate Key Metrics in Seconds

Get comprehensive evaluation metrics with just 3 lines of code—no configuration required:

```python
from blazemetrics import BlazeMetricsClient

candidates = ["The quick brown fox.", "Hello world!"]
references = [["The fast brown fox."], ["Hello world."]]

client = BlazeMetricsClient()
metrics = client.compute_metrics(candidates, references)
print(metrics)  # {'rouge1_f1': [...], 'bleu': [...], ...}

aggregated = client.aggregate_metrics(metrics)
print(aggregated)  # {'rouge1_f1': 0.85, ...}
```

---

## Complete LLM Workflow: Metrics, Guardrails, Analytics, and Factuality

Comprehensive evaluation pipeline combining traditional metrics, safety guardrails, real-time analytics, and LLM-based factuality scoring:

```python
from blazemetrics import BlazeMetricsClient
from blazemetrics.llm_judge import LLMJudge

# Sample LLM generations and ground truth references
candidates = ["Alice's email is alice@example.com.", "2 + 2 is 5."]
references = [["Her email is alice@example.com."], ["2 + 2 = 4"]]

# Initialize client with comprehensive configuration
client = BlazeMetricsClient(
    blocklist=["bitcoin"],
    redact_pii=True,
    regexes=[r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"],
    enable_analytics=True,
    metrics_lowercase=True,
)

# 1. Compute traditional NLP metrics
metrics = client.compute_metrics(candidates, references)
aggregated_metrics = client.aggregate_metrics(metrics)

# 2. Run safety and guardrail checks
violations = client.check_safety(candidates)

# 3. Update analytics and get trend analysis
client.add_metrics(aggregated_metrics)
analytics_summary = client.get_analytics_summary()

# 4. LLM-based factuality scoring (requires OpenAI API key)
judge = LLMJudge(provider="openai", api_key="YOUR_OPENAI_KEY", model="gpt-4o")

def factuality_scorer(output, reference):
    result = judge.score([output], [reference])
    return {"factuality": result[0].get("faithfulness", 0.0)}

client.set_factuality_scorer(factuality_scorer)
factuality_scores = client.evaluate_factuality(candidates, [r[0] for r in references])

# 5. Generate comprehensive model evaluation report
model_card = client.generate_model_card(
    "my-llm", 
    metrics, 
    analytics_summary, 
    config=vars(client.config),
    violations=violations, 
    factuality=factuality_scores
)
print(model_card)
```

---

## Integration Examples

BlazeMetrics integrates seamlessly with popular ML and LLM frameworks:

- **LLM Providers**: Drop-in evaluation for HuggingFace, OpenAI, Anthropic, LangChain workflows
- **RAG Systems**: Built-in support with `semantic_search`, `agentic_rag_evaluate`, and provenance tracking
- **Real-time Monitoring**: Live dashboards via `blazemetrics-dashboard` (available with `[dashboard]` installation)
- **Export Formats**: Built-in exporters for Prometheus, StatsD, CSV, and HTML reports

For detailed integration examples, check our [real-world use cases](https://2796gaurav.github.io/blazemetrics/use-cases).

---

## Advanced Features

### Parallel and Asynchronous Processing
```python
# Parallel evaluation for large datasets
parallel_metrics = client.compute_metrics_parallel(candidates, references)

# Asynchronous processing for non-blocking evaluation
async_metrics = await client.compute_metrics_async(candidates, references)
```

### Real-time Analytics and Monitoring
```python
# Streaming analytics with anomaly detection
client.add_metrics_sample(sample_metrics)
anomalies = client.detect_anomalies()
trends = client.get_trends()
```

### Interactive Dashboards
After installing with dashboard support:
```bash
blazemetrics-dashboard
```
Or embed the dashboard server in your WSGI application pipeline.

### RAG and Agent Evaluation
```python
# Evaluate RAG systems and agent workflows
rag_results = client.agentic_rag_evaluate(
    queries=queries,
    contexts=contexts,
    answers=answers,
    ground_truths=ground_truths
)
```

---

## Configuration Options

The `BlazeMetricsClient` supports extensive configuration options:

**Metrics Configuration**:
- `metrics_include`: Specify which metrics to compute
- `metrics_lowercase`: Enable lowercase normalization
- `metrics_stemming`: Apply stemming to text

**Guardrails and Safety**:
- `blocklist`: Custom blocked terms and phrases
- `regexes`: Custom regex patterns for validation
- `redact_pii`: Automatic PII detection and redaction
- `case_insensitive`: Case-insensitive pattern matching

**Analytics and Monitoring**:
- `enable_analytics`: Real-time analytics tracking
- `analytics_window`: Sliding window for trend analysis
- `analytics_alerts`: Threshold-based alerting
- `analytics_anomalies`: Anomaly detection settings

**Performance Optimization**:
- `parallel_processing`: Enable parallel computation
- `max_workers`: Maximum worker threads for parallel processing

**Export and Integration**:
- `enable_monitoring`: Export metrics to monitoring systems
- `prometheus_gateway`: Prometheus pushgateway integration
- `statsd_addr`: StatsD server address for metrics export

For complete configuration details, visit our [documentation](https://2796gaurav.github.io/blazemetrics/docs).

---

## Resources and Learning

- **Getting Started**: [Learning Paths](https://2796gaurav.github.io/blazemetrics/learning-paths)
- **API Documentation**: [Complete API Reference](https://2796gaurav.github.io/blazemetrics/docs)
- **LLM Integration**: [LLM Usage Guide](https://2796gaurav.github.io/blazemetrics/llm-usage)
- **Production Deployment**: [Real World Use Cases](https://2796gaurav.github.io/blazemetrics/use-cases)
- **Performance Analysis**: [Benchmarks and Comparisons](https://2796gaurav.github.io/blazemetrics/benchmarks)

---

## Contributing and Community

We welcome contributions from the community! Here's how you can get involved:

- **Star the project** on [GitHub](https://github.com/2796gaurav/blazemetrics) to show your support
- **Report issues** or submit feature requests via GitHub Issues
- **Contribute code** by creating pull requests
- **Join discussions** and help evolve LLM benchmarking and safety standards

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**BlazeMetrics** © 2025 by [Gaurav](mailto:2796gaurav@gmail.com)
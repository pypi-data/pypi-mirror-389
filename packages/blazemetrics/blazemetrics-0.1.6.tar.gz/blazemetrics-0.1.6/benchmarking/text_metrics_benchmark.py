import time
import string
import json
import psutil
import os
from typing import Dict, List, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from blazemetrics import BlazeMetricsClient
import traceback
import warnings
warnings.filterwarnings("ignore")

print("Loading evaluation libraries for direct comparison...")

# --- Library Loading ---
_evaluate_cache = None
_sacrebleu_cache = None
_nltk_cache = None
_torchmetrics_cache = None

def get_evaluate():
    """Checks if HuggingFace Evaluate is available and caches the module."""
    global _evaluate_cache
    if _evaluate_cache is None:
        try:
            import evaluate
            _evaluate_cache = evaluate
            print("    HuggingFace Evaluate loaded")
        except ImportError as e:
            print(f"    HuggingFace Evaluate not available: {e}")
            _evaluate_cache = False
    return _evaluate_cache if _evaluate_cache is not False else None

def get_sacrebleu():
    """Load SacreBLEU"""
    global _sacrebleu_cache
    if _sacrebleu_cache is None:
        try:
            import sacrebleu
            _sacrebleu_cache = sacrebleu
            print("    SacreBLEU loaded")
        except ImportError:
            print("    SacreBLEU not available")
            _sacrebleu_cache = False
    return _sacrebleu_cache if _sacrebleu_cache is not False else None

def get_nltk():
    """Load NLTK"""
    global _nltk_cache
    if _nltk_cache is None:
        try:
            import nltk
            from nltk.translate.meteor_score import meteor_score
            from nltk.translate.bleu_score import sentence_bleu
            from nltk.translate.chrf_score import sentence_chrf
            
            required_data = ['punkt', 'wordnet', 'omw-1.4']
            for data_name in required_data:
                try:
                    nltk.data.find(f'tokenizers/{data_name}' if 'punkt' in data_name else f'corpora/{data_name}.zip')
                except LookupError:
                    try:
                        nltk.download(data_name, quiet=True)
                    except Exception as e:
                        print(f"    Warning: NLTK failed to download '{data_name}': {e}")

            _nltk_cache = {
                'nltk': nltk,
                'meteor_score': meteor_score,
                'sentence_bleu': sentence_bleu,
                'sentence_chrf': sentence_chrf
            }
            print("    NLTK loaded")
        except ImportError as e:
            print(f"    NLTK not available: {e}")
            _nltk_cache = False
    return _nltk_cache if _nltk_cache is not False else None

def get_torchmetrics():
    """Load TorchMetrics"""
    global _torchmetrics_cache
    if _torchmetrics_cache is None:
        try:
            import torchmetrics
            from torchmetrics.text import BLEUScore, ROUGEScore
            _torchmetrics_cache = {
                'torchmetrics': torchmetrics,
                'BLEUScore': BLEUScore,
                'ROUGEScore': ROUGEScore
            }
            print("    TorchMetrics loaded")
        except ImportError:
            print("    TorchMetrics not available")
            _torchmetrics_cache = False
    return _torchmetrics_cache if _torchmetrics_cache is not False else None

# Initialize all libraries
evaluate_module = get_evaluate()
sacrebleu = get_sacrebleu()
nltk_modules = get_nltk()
torchmetrics_modules = get_torchmetrics()

print("Library loading complete!\n")

# --- Resource Monitoring ---
class ResourceMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = None
        self.start_time = None

    def start_monitoring(self):
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_time = time.perf_counter()

    def get_resource_usage(self):
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        return {
            'memory_used_mb': max(0, current_memory - self.start_memory) if self.start_memory else 0,
            'execution_time': time.perf_counter() - self.start_time if self.start_time else 0
        }

# --- Data Generation ---
def normalize_text(s):
    """Optimized text normalization"""
    if not hasattr(normalize_text, '_table'):
        normalize_text._table = str.maketrans('', '', string.punctuation)
    return s.lower().translate(normalize_text._table)

def make_diverse_batch(size=1000):
    """Create more diverse test data"""
    import random
    
    templates = [
        "The {adj} {animal} {verb} over the {adj2} {object}",
        "A {adj} day brings {adj2} opportunities to {verb}",
        "Scientists discovered that {animal} can {verb} better than expected",
    ]
    
    adj_list = ["quick", "fast", "slow", "bright", "dark", "large", "small", "amazing"]
    animals = ["fox", "dog", "cat", "bird", "lion", "elephant", "rabbit", "deer"]
    verbs = ["jumps", "runs", "flies", "moves", "travels", "explores", "discovers", "creates"]
    objects = ["tree", "house", "mountain", "river", "building", "bridge", "garden", "forest"]
    
    candidates = []
    references = []
    
    for i in range(size):
        template = random.choice(templates)
        shared_params = {
            "adj": random.choice(adj_list), "adj2": random.choice(adj_list),
            "animal": random.choice(animals), "verb": random.choice(verbs),
            "object": random.choice(objects)
        }
        candidate = template.format(**shared_params) + f" number {i}"
        ref1 = template.format(**shared_params) + f" number {i}"
        ref2 = template.format(**shared_params) + f" number {i}"
        
        candidates.append(candidate)
        references.append([ref1, ref2])
    
    return candidates, references

_data_cache = {}
def get_test_data(batch_size=2, normalize=True):
    """Enhanced test data generation with caching"""
    cache_key = (batch_size, normalize)
    if cache_key in _data_cache:
        return _data_cache[cache_key]

    candidates, references = make_diverse_batch(batch_size)

    if normalize:
        candidates = [normalize_text(c) for c in candidates]
        references = [[normalize_text(r) for r in refs] for refs in references]

    result = (candidates, references)
    _data_cache[cache_key] = result
    return result

# --- Benchmark Functions ---

def benchmark_blazemetrics(batch_size=2, normalize_data=True):
    """BlazeMetrics benchmark"""
    monitor = ResourceMonitor()
    monitor.start_monitoring()

    client = BlazeMetricsClient()
    candidates, references = get_test_data(batch_size, normalize=normalize_data)

    start_time = time.perf_counter()
    results = client.compute_metrics(
        candidates, references,
        include=["rouge1", "rouge2", "rougeL", "bleu", "meteor", "wer", "chrf"],
        lowercase=not normalize_data
    )
    end_time = time.perf_counter()

    aggs = client.aggregate_metrics(results)
    resources = monitor.get_resource_usage()

    return {
        'aggregate': aggs,
        'execution_time': end_time - start_time,
        'package': 'BlazeMetrics',
        'batch_size': len(candidates),
        'resources': resources,
    }

def benchmark_huggingface_evaluate(batch_size=2, normalize_data=True):
    """HuggingFace Evaluate benchmark"""
    if not evaluate_module: raise RuntimeError("HuggingFace Evaluate not available")
    
    monitor = ResourceMonitor()
    monitor.start_monitoring()

    candidates, references = get_test_data(batch_size, normalize=normalize_data)
    
    rouge_metric = evaluate_module.load('rouge')
    bleu_metric = evaluate_module.load('bleu')
    meteor_metric = evaluate_module.load('meteor')
    chrf_metric = evaluate_module.load('chrf')

    start_time = time.perf_counter()
    metrics_results = {}
    
    metrics_results.update(rouge_metric.compute(predictions=candidates, references=references, use_stemmer=False) or {})
    metrics_results.update(bleu_metric.compute(predictions=candidates, references=references) or {})
    metrics_results.update(meteor_metric.compute(predictions=candidates, references=references) or {})
    metrics_results.update(chrf_metric.compute(predictions=candidates, references=references) or {})
    
    end_time = time.perf_counter()
    resources = monitor.get_resource_usage()

    return {
        'metrics': metrics_results,
        'execution_time': end_time - start_time,
        'package': 'Huggingface Evaluate',
        'batch_size': len(candidates),
        'resources': resources,
    }

def benchmark_sacrebleu(batch_size=2, normalize_data=True):
    """SacreBLEU benchmark"""
    if not sacrebleu: raise RuntimeError("SacreBLEU not available")
    
    monitor = ResourceMonitor()
    monitor.start_monitoring()

    candidates, references = get_test_data(batch_size, normalize=normalize_data)
    refs_transposed = list(zip(*references))

    start_time = time.perf_counter()
    
    bleu_score = sacrebleu.corpus_bleu(candidates, refs_transposed)
    chrf_score = sacrebleu.corpus_chrf(candidates, refs_transposed)
    
    end_time = time.perf_counter()
    resources = monitor.get_resource_usage()

    return {
        'metrics': {'bleu': bleu_score.score, 'chrf': chrf_score.score},
        'execution_time': end_time - start_time,
        'package': 'SacreBLEU',
        'batch_size': len(candidates),
        'resources': resources,
    }

def benchmark_nltk(batch_size=2, normalize_data=True):
    """NLTK benchmark"""
    if not nltk_modules: raise RuntimeError("NLTK not available")

    monitor = ResourceMonitor()
    monitor.start_monitoring()

    candidates, references = get_test_data(batch_size, normalize=normalize_data)
    
    start_time = time.perf_counter()
    
    refs_tokens = [[ref.split() for ref in refs] for refs in references]
    cand_tokens = [cand.split() for cand in candidates]

    bleu_scores = [nltk_modules['sentence_bleu'](ref_tokens, cand_token) for cand_token, ref_tokens in zip(cand_tokens, refs_tokens)]
    meteor_scores = [nltk_modules['meteor_score'](ref_tokens, cand_token) for cand_token, ref_tokens in zip(cand_tokens, refs_tokens)]
    chrf_scores = [nltk_modules['sentence_chrf'](refs[0], cand) for cand, refs in zip(candidates, references)]

    end_time = time.perf_counter()
    resources = monitor.get_resource_usage()

    return {
        'metrics': {
            'bleu': sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0,
            'meteor': sum(meteor_scores) / len(meteor_scores) if meteor_scores else 0,
            'chrf': sum(chrf_scores) / len(chrf_scores) if chrf_scores else 0,
        },
        'execution_time': end_time - start_time,
        'package': 'NLTK',
        'batch_size': len(candidates),
        'resources': resources,
    }


def benchmark_torchmetrics(batch_size=2, normalize_data=True):
    """TorchMetrics benchmark"""
    if not torchmetrics_modules: raise RuntimeError("TorchMetrics not available")
    
    monitor = ResourceMonitor()
    monitor.start_monitoring()

    candidates, references = get_test_data(batch_size, normalize=normalize_data)
    
    start_time = time.perf_counter()
    
    bleu_metric = torchmetrics_modules['BLEUScore']()
    bleu_score = bleu_metric(candidates, list(zip(*references)))
    
    rouge_metric = torchmetrics_modules['ROUGEScore']()
    rouge_scores = rouge_metric(candidates, references)
    
    end_time = time.perf_counter()
    resources = monitor.get_resource_usage()

    return {
        'metrics': {'bleu': float(bleu_score), **{k: float(v) for k, v in rouge_scores.items()}},
        'execution_time': end_time - start_time,
        'package': 'TorchMetrics',
        'batch_size': len(candidates),
        'resources': resources,
    }


# --- Results Display ---
def print_results(results: List[Dict], batch_size: int):
    """Print benchmark results"""
    print(f"\n--- BENCHMARK RESULTS (Batch Size: {batch_size}) ---")
    print("=" * 70)
    print(f"{'Package':<28} {'Time (s)':<12} {'Memory (MB)':<12}")
    print("-" * 70)

    sorted_results = sorted([r for r in results if 'error' not in r], key=lambda x: x['execution_time'])
    
    for result in sorted_results:
        package = result['package']
        exec_time = result['execution_time']
        memory = result.get('resources', {}).get('memory_used_mb', 0)
        print(f"{package:<28} {exec_time:<12.4f} {memory:<12.1f}")
    
    for result in [r for r in results if 'error' in r]:
        print(f"{result['package']:<28} {'ERROR':<12} {'N/A':<12}")

def print_speed_comparison(results: List[Dict]):
    """Print speed comparison against BlazeMetrics"""
    valid_results = [r for r in results if 'error' not in r]
    blazemetrics_result = next((r for r in valid_results if 'BlazeMetrics' in r['package']), None)
    if not blazemetrics_result: return

    blazemetrics_time = blazemetrics_result['execution_time']
    print(f"\nSPEED COMPARISON vs BlazeMetrics ({blazemetrics_time:.4f}s):")
    print("-" * 60)

    for result in sorted(valid_results, key=lambda x: x['execution_time']):
        ratio = result['execution_time'] / blazemetrics_time
        status = "BASELINE" if 'BlazeMetrics' in result['package'] else "SLOWER" if ratio > 1 else "FASTER"
        print(f"{status:<10} {result['package']:<28} {ratio:>6.2f}x")


# --- Main Benchmark Runner ---
def run_benchmarks(batch_sizes: List[int], repeats: int = 3) -> Dict[int, List[Dict]]:
    """Run a focused benchmark on comparable libraries."""
    all_results: Dict[int, List[Dict]] = {}

    benchmarks_to_run = {
        'BlazeMetrics': benchmark_blazemetrics,
        'Huggingface Evaluate': benchmark_huggingface_evaluate,
        'SacreBLEU': benchmark_sacrebleu,
        'NLTK': benchmark_nltk,
        'TorchMetrics': benchmark_torchmetrics,
    }
    
    availability_map = {
        'BlazeMetrics': True,
        'Huggingface Evaluate': bool(evaluate_module),
        'SacreBLEU': bool(sacrebleu),
        'NLTK': bool(nltk_modules),
        'TorchMetrics': bool(torchmetrics_modules),
    }

    for batch_size in batch_sizes:
        print(f"\n{'='*20} RUNNING FOR BATCH SIZE: {batch_size} {'='*20}")
        batch_results = []
        
        for name, func in benchmarks_to_run.items():
            if not availability_map[name]:
                print(f"   Skipping {name} (not available)...")
                continue
            
            try:
                print(f"   Running {name}...", end=' ', flush=True)
                times = []
                last_result = None
                for _ in range(repeats):
                    res = func(batch_size=batch_size, normalize_data=True)
                    times.append(res['execution_time'])
                    last_result = res
                
                last_result['execution_time'] = sorted(times)[len(times) // 2] # Median
                batch_results.append(last_result)
                print(f"{last_result['execution_time']:.4f}s")
            
            except Exception as e:
                batch_results.append({'error': str(e), 'package': name})
                print(f"Failed: {e}")
                traceback.print_exc()

        all_results[batch_size] = batch_results
        print_results(batch_results, batch_size)
        print_speed_comparison(batch_results)

    return all_results

def create_plots(all_results: Dict[int, List[Dict]]):
    """Create visualization plots from benchmark results."""
    if not all_results: return
    
    largest_batch_size = max(all_results.keys())
    results_for_plot = [r for r in all_results[largest_batch_size] if 'error' not in r]
    
    if not results_for_plot:
        print("No successful runs to plot.")
        return

    plot_data = sorted(results_for_plot, key=lambda x: x['execution_time'])

    packages = [d['package'] for d in plot_data]
    times = [d['execution_time'] for d in plot_data]
    mems = [d.get('resources', {}).get('memory_used_mb', 0) for d in plot_data]
    
    # Define colors for the execution time bar chart
    time_bar_colors = ['red' if pkg == 'BlazeMetrics' else 'lightgray' for pkg in packages]

    fig = make_subplots(rows=1, cols=2, subplot_titles=(f"Execution Time (Batch: {largest_batch_size})", f"Memory Usage (Batch: {largest_batch_size})"))
    
    # Add execution time bar chart with custom colors
    fig.add_trace(go.Bar(
        x=packages, 
        y=times, 
        name="Time", 
        text=[f'{t:.3f}s' for t in times],
        marker_color=time_bar_colors
    ), row=1, col=1)
    
    # Add memory usage bar chart
    fig.add_trace(go.Bar(x=packages, y=mems, name="Memory", text=[f'{m:.1f}MB' for m in mems]), row=1, col=2)

    fig.update_layout(title_text=f"Direct Comparison Benchmark (Batch Size: {largest_batch_size})", showlegend=False, height=600)
    fig.update_xaxes(tickangle=-45)
    fig.update_yaxes(title_text="Time (seconds)", type="log", row=1, col=1)
    fig.update_yaxes(title_text="Memory (MB)", row=1, col=2)
    
    output_path = "benchmark_results.html"
    fig.write_html(output_path, auto_open=False)
    print(f"\nPlots saved to {output_path}")
    return output_path

# --- Main Execution ---
if __name__ == "__main__":
    print("NLP METRICS BENCHMARK SUITE")
    print("=" * 50)

    BATCH_SIZES = [10000]
    REPEATS = 3

    try:
        results = run_benchmarks(BATCH_SIZES, REPEATS)
        if results and any('error' not in r for r in next(iter(results.values()))):
            plot_path = create_plots(results)
            print("\n" + "="*50)
            print("BENCHMARK SUITE COMPLETED")
            print(f"Plots saved to: {plot_path}")
            print("="*50)
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        traceback.print_exc()
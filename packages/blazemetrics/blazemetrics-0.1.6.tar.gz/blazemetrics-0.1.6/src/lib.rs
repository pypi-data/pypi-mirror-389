use pyo3::prelude::*;
use numpy::PyReadonlyArray2;
use ndarray::{Axis, Array2, ArrayView2};
use rayon::prelude::*;

mod common;
mod rouge;
mod bleu;
mod chrf;
mod similarity;
mod wer;
mod meteor_metric;
mod moverscore;
mod guardrails;
mod fuzzy;
mod embeddings;
mod ann_hnsw;

mod agentic_rag;
mod multimodal;
mod agent_eval;
mod production_monitor;
mod safety;
mod code_eval;

use crate::agentic_rag::agentic_rag_evaluate;
use crate::multimodal::{multimodal_evaluate, multimodal_evaluate_generation};
use crate::agent_eval::agent_eval_evaluate;
use crate::production_monitor::production_monitor_tick;
use crate::safety::safety_comprehensive_evaluation;
use crate::code_eval::code_eval_evaluate;


// Wrapper for ROUGE scores
#[pyfunction]
fn rouge_score(
    py: Python,
    candidates: Vec<String>,
    references: Vec<Vec<String>>,
    score_type: &str,
    n: Option<usize>,
) -> PyResult<Vec<(f64, f64, f64)>> {
    let result = py.allow_threads(|| {
        match score_type {
            "rouge_n" => {
                let n_val = n.unwrap_or(1);
                common::parallel_process(&candidates, &references, |c, r| rouge::rouge_n(c, r, n_val))
            }
            "rouge_l" => {
                common::parallel_process(&candidates, &references, rouge::rouge_l)
            }
            _ => panic!("Invalid ROUGE type. Use 'rouge_n' or 'rouge_l'."),
        }
    });
    Ok(result)
}

// Wrapper for BLEU score
#[pyfunction(name = "bleu")]
fn bleu_score_py(
    py: Python,
    candidates: Vec<String>,
    references: Vec<Vec<String>>,
    max_n: Option<usize>,
) -> PyResult<Vec<f64>> {
    let n = max_n.unwrap_or(4);
    let result = py.allow_threads(|| {
        common::parallel_process(&candidates, &references, |c, r| bleu::bleu_score(c, r, n))
    });
    Ok(result)
}

// chrF metric
#[pyfunction]
fn chrf_score(
    py: Python,
    candidates: Vec<String>,
    references: Vec<Vec<String>>,
    max_n: Option<usize>,
    beta: Option<f64>,
) -> PyResult<Vec<f64>> {
    let n = max_n.unwrap_or(6);
    let b = beta.unwrap_or(2.0);
    let result = py.allow_threads(|| {
        common::parallel_process(&candidates, &references, |c, r| chrf::chrf(c, r, n, b))
    });
    Ok(result)
}

// Token-level F1
#[pyfunction]
fn token_f1(
    py: Python,
    candidates: Vec<String>,
    references: Vec<Vec<String>>,
) -> PyResult<Vec<f64>> {
    let result = py.allow_threads(|| {
        common::parallel_process(&candidates, &references, |c, r| similarity::token_f1_best(c, r))
    });
    Ok(result)
}

// Jaccard similarity over tokens
#[pyfunction]
fn jaccard(
    py: Python,
    candidates: Vec<String>,
    references: Vec<Vec<String>>,
) -> PyResult<Vec<f64>> {
    let result = py.allow_threads(|| {
        common::parallel_process(&candidates, &references, |c, r| similarity::jaccard_best(c, r))
    });
    Ok(result)
}

// Highly optimized BERTScore similarity calculation (synchronous)
#[pyfunction]
fn bert_score_similarity(
    _py: Python,
    candidates: PyReadonlyArray2<'_, f32>,
    references: PyReadonlyArray2<'_, f32>,
) -> PyResult<(f32, f32, f32)> {
    let cands_view = candidates.as_array();
    let refs_view = references.as_array();

    // Normalize embeddings
    let cands_norm = normalize_embeddings(cands_view);
    let refs_norm = normalize_embeddings(refs_view);

    // Cosine similarity via matrix multiplication
    let similarity_matrix = cands_norm.dot(&refs_view.t());

    // Get max similarity for each token
    let precision_scores: Vec<f32> = similarity_matrix
        .axis_iter(Axis(0))
        .into_par_iter()
        .map(|row| row.fold(f32::NEG_INFINITY, |a, &b| a.max(b)))
        .collect();
    
    let recall_scores: Vec<f32> = similarity_matrix
        .axis_iter(Axis(1))
        .into_par_iter()
        .map(|col| col.fold(f32::NEG_INFINITY, |a, &b| a.max(b)))
        .collect();

    let p_mean = if precision_scores.is_empty() { 0.0 } else { precision_scores.iter().sum::<f32>() / precision_scores.len() as f32 };
    let r_mean = if recall_scores.is_empty() { 0.0 } else { recall_scores.iter().sum::<f32>() / recall_scores.len() as f32 };
    let f1 = if p_mean + r_mean == 0.0 { 0.0 } else { 2.0 * p_mean * r_mean / (p_mean + r_mean) };

    Ok((p_mean, r_mean, f1))
}

// MoverScore (greedy variant)
#[pyfunction]
fn moverscore_greedy_py(
    _py: Python,
    candidates: PyReadonlyArray2<'_, f32>,
    references: PyReadonlyArray2<'_, f32>,
) -> PyResult<(f32, f32, f32)> {
    let c = candidates.as_array();
    let r = references.as_array();
    Ok(moverscore::moverscore_greedy(c, r))
}

// METEOR-lite
#[pyfunction(name = "meteor")]
fn meteor_score(
    py: Python,
    candidates: Vec<String>,
    references: Vec<Vec<String>>,
    alpha: Option<f64>,
    beta: Option<f64>,
    gamma: Option<f64>,
) -> PyResult<Vec<f64>> {
    let a = alpha.unwrap_or(0.9);
    let b = beta.unwrap_or(3.0);
    let g = gamma.unwrap_or(0.5);
    let result = py.allow_threads(|| {
        common::parallel_process(&candidates, &references, |c, r| meteor_metric::meteor_lite(c, r, a, b, g))
    });
    Ok(result)
}

// WER
#[pyfunction(name = "wer")]
fn wer_score(
    py: Python,
    candidates: Vec<String>,
    references: Vec<Vec<String>>,
) -> PyResult<Vec<f64>> {
    let result = py.allow_threads(|| {
        common::parallel_process(&candidates, &references, |c, r| wer::wer(c, r))
    });
    Ok(result)
}

// Guardrails exposed functions
#[pyfunction]
fn guard_blocklist(
    py: Python,
    texts: Vec<String>,
    patterns: Vec<String>,
    case_insensitive: Option<bool>,
) -> PyResult<Vec<bool>> {
    let ci = case_insensitive.unwrap_or(true);
    let result = py.allow_threads(|| {
        let cfg = guardrails::BlocklistConfig { patterns, case_insensitive: ci };
        guardrails::blocklist_any(&texts, &cfg)
    });
    Ok(result)
}

#[pyfunction]
fn guard_regex(
    py: Python,
    texts: Vec<String>,
    patterns: Vec<String>,
    case_insensitive: Option<bool>,
) -> PyResult<Vec<bool>> {
    let ci = case_insensitive.unwrap_or(true);
    let result = py.allow_threads(|| {
        let cfg = guardrails::RegexConfig { patterns, case_insensitive: ci };
        guardrails::regex_any(&texts, &cfg)
    });
    Ok(result)
}

#[pyfunction]
fn guard_pii_redact(py: Python, texts: Vec<String>) -> PyResult<Vec<String>> {
    let result = py.allow_threads(|| guardrails::pii_redact(&texts));
    Ok(result)
}

#[pyfunction]
fn guard_safety_score(py: Python, texts: Vec<String>) -> PyResult<Vec<f32>> {
    let result = py.allow_threads(|| guardrails::safety_score_quick(&texts));
    Ok(result)
}

// New LLM-specific guardrails
#[pyfunction]
fn guard_json_validate(
    py: Python,
    texts: Vec<String>,
    schema_json: String,
) -> PyResult<(Vec<bool>, Vec<String>)> {
    let result = py.allow_threads(|| guardrails::json_validate(&texts, &schema_json));
    Ok(result)
}

#[pyfunction]
fn guard_detect_injection_spoof(py: Python, texts: Vec<String>) -> PyResult<Vec<bool>> {
    let result = py.allow_threads(|| guardrails::detect_injection_spoof(&texts));
    Ok(result)
}

#[pyfunction]
fn guard_max_cosine_similarity(
    _py: Python,
    candidates: PyReadonlyArray2<'_, f32>,
    exemplars: PyReadonlyArray2<'_, f32>,
) -> PyResult<Vec<f32>> {
    let c: Vec<Vec<f32>> = candidates.as_array().rows().into_iter().map(|r| r.to_vec()).collect();
    let e: Vec<Vec<f32>> = exemplars.as_array().rows().into_iter().map(|r| r.to_vec()).collect();
    Ok(guardrails::max_cosine_similarity(&c, &e))
}

// New fuzzy matching functions
#[pyfunction]
fn guard_fuzzy_blocklist(
    py: Python,
    texts: Vec<String>,
    patterns: Vec<String>,
    max_distance: Option<usize>,
    algorithm: Option<&str>,
    case_sensitive: Option<bool>,
) -> PyResult<Vec<bool>> {
    let max_dist = max_distance.unwrap_or(2);
    let algo = match algorithm.unwrap_or("levenshtein") {
        "levenshtein" => fuzzy::FuzzyAlgorithm::Levenshtein,
        "damerau_levenshtein" => fuzzy::FuzzyAlgorithm::DamerauLevenshtein,
        "jaro_winkler" => fuzzy::FuzzyAlgorithm::JaroWinkler,
        _ => fuzzy::FuzzyAlgorithm::Levenshtein,
    };
    let case_sens = case_sensitive.unwrap_or(false);
    
    let config = fuzzy::FuzzyConfig {
        max_distance: max_dist,
        algorithm: algo,
        case_sensitive: case_sens,
        normalize_whitespace: true,
    };
    
    let result = py.allow_threads(|| {
        fuzzy::fuzzy_match_any_bool(&texts, &patterns, &config)
    });
    Ok(result)
}

#[pyfunction]
fn guard_fuzzy_blocklist_detailed(
    py: Python,
    texts: Vec<String>,
    patterns: Vec<String>,
    max_distance: Option<usize>,
    algorithm: Option<&str>,
    case_sensitive: Option<bool>,
) -> PyResult<Vec<Vec<(String, String, f64, f64, String)>>> {
    let max_dist = max_distance.unwrap_or(2);
    let algo = match algorithm.unwrap_or("levenshtein") {
        "levenshtein" => fuzzy::FuzzyAlgorithm::Levenshtein,
        "damerau_levenshtein" => fuzzy::FuzzyAlgorithm::DamerauLevenshtein,
        "jaro_winkler" => fuzzy::FuzzyAlgorithm::JaroWinkler,
        _ => fuzzy::FuzzyAlgorithm::Levenshtein,
    };
    let case_sens = case_sensitive.unwrap_or(false);
    
    let config = fuzzy::FuzzyConfig {
        max_distance: max_dist,
        algorithm: algo,
        case_sensitive: case_sens,
        normalize_whitespace: true,
    };
    
    let result = py.allow_threads(|| {
        let matches = fuzzy::fuzzy_match_any(&texts, &patterns, &config);
        // Convert FuzzyMatch to tuple format that PyO3 can handle
        matches.into_iter().map(|text_matches| {
            text_matches.into_iter().map(|m| {
                let algorithm_str = match m.algorithm {
                    fuzzy::FuzzyAlgorithm::Levenshtein => "levenshtein",
                    fuzzy::FuzzyAlgorithm::DamerauLevenshtein => "damerau_levenshtein",
                    fuzzy::FuzzyAlgorithm::JaroWinkler => "jaro_winkler",
                }.to_string();
                (m.pattern, m.text, m.distance, m.similarity, algorithm_str)
            }).collect()
        }).collect()
    });
    Ok(result)
}

// New embedding operations
#[pyfunction]
fn batch_cosine_similarity_optimized(
    _py: Python,
    embeddings: PyReadonlyArray2<'_, f32>,
    query: PyReadonlyArray2<'_, f32>,
) -> PyResult<Vec<f32>> {
    let emb_array = embeddings.as_array();
    let query_array = query.as_array();
    
    let embeddings_vec: Vec<Vec<f32>> = emb_array.rows().into_iter().map(|r| r.to_vec()).collect();
    let query_vec: Vec<f32> = query_array.row(0).to_vec();
    
    let result = embeddings::batch_cosine_similarity_simple(&embeddings_vec, &query_vec);
    Ok(result)
}

#[pyfunction]
fn semantic_search_topk(
    _py: Python,
    queries: PyReadonlyArray2<'_, f32>,
    corpus: PyReadonlyArray2<'_, f32>,
    top_k: usize,
) -> PyResult<Vec<Vec<(usize, f32)>>> {
    let queries_array = queries.as_array();
    let corpus_array = corpus.as_array();
    
    let queries_vec: Vec<Vec<f32>> = queries_array.rows().into_iter().map(|r| r.to_vec()).collect();
    let corpus_vec: Vec<Vec<f32>> = corpus_array.rows().into_iter().map(|r| r.to_vec()).collect();
    
    let result = embeddings::advanced_ops::semantic_search_topk(&queries_vec, &corpus_vec, top_k);
    Ok(result)
}

#[pyfunction]
fn rag_retrieval_with_reranking(
    _py: Python,
    query: PyReadonlyArray2<'_, f32>,
    passages: PyReadonlyArray2<'_, f32>,
    top_k: usize,
    rerank_threshold: f32,
) -> PyResult<Vec<(usize, f32, f32)>> {
    let query_array = query.as_array();
    let passages_array = passages.as_array();
    
    let query_vec: Vec<f32> = query_array.row(0).to_vec();
    let passages_vec: Vec<Vec<f32>> = passages_array.rows().into_iter().map(|r| r.to_vec()).collect();
    
    let result = embeddings::rag_ops::rag_retrieval_with_reranking(&query_vec, &passages_vec, top_k, rerank_threshold);
    Ok(result)
}

// Helper for normalizing embeddings
fn normalize_embeddings(embeddings: ArrayView2<f32>) -> Array2<f32> {
    let mut normalized_embeddings = embeddings.to_owned();
    normalized_embeddings
        .axis_iter_mut(Axis(0))
        .into_par_iter()
        .for_each(|mut row| {
            let norm = row.dot(&row).sqrt();
            if norm > 1e-9 {
                row /= norm;
            }
        });
    normalized_embeddings
}

#[pymodule]
fn blazemetrics_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rouge_score, m)?)?;
    m.add_function(wrap_pyfunction!(bleu_score_py, m)?)?;
    m.add_function(wrap_pyfunction!(chrf_score, m)?)?;
    m.add_function(wrap_pyfunction!(token_f1, m)?)?;
    m.add_function(wrap_pyfunction!(jaccard, m)?)?;
    m.add_function(wrap_pyfunction!(bert_score_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(moverscore_greedy_py, m)?)?;
    m.add_function(wrap_pyfunction!(meteor_score, m)?)?;
    m.add_function(wrap_pyfunction!(wer_score, m)?)?;
    
    // Guardrails
    m.add_function(wrap_pyfunction!(guard_blocklist, m)?)?;
    m.add_function(wrap_pyfunction!(guard_regex, m)?)?;
    m.add_function(wrap_pyfunction!(guard_pii_redact, m)?)?;
    m.add_function(wrap_pyfunction!(guard_safety_score, m)?)?;
    m.add_function(wrap_pyfunction!(guard_json_validate, m)?)?;
    m.add_function(wrap_pyfunction!(guard_detect_injection_spoof, m)?)?;
    m.add_function(wrap_pyfunction!(guard_max_cosine_similarity, m)?)?;
    
    // New fuzzy matching functions
    m.add_function(wrap_pyfunction!(guard_fuzzy_blocklist, m)?)?;
    m.add_function(wrap_pyfunction!(guard_fuzzy_blocklist_detailed, m)?)?;
    
    // New embedding operations
    m.add_function(wrap_pyfunction!(batch_cosine_similarity_optimized, m)?)?;
    m.add_function(wrap_pyfunction!(semantic_search_topk, m)?)?;
    m.add_function(wrap_pyfunction!(rag_retrieval_with_reranking, m)?)?;

    // ANN/HNSW functions
    m.add_function(wrap_pyfunction!(ann_hnsw::ann_build_index, m)?)?;
    m.add_function(wrap_pyfunction!(ann_hnsw::ann_query_topk, m)?)?;
    m.add_function(wrap_pyfunction!(ann_hnsw::ann_add_docs, m)?)?;
    m.add_function(wrap_pyfunction!(ann_hnsw::ann_save_index, m)?)?;
    m.add_function(wrap_pyfunction!(ann_hnsw::ann_load_index, m)?)?;
    
    m.add_function(wrap_pyfunction!(agentic_rag_evaluate, m)?)?;
    m.add_function(wrap_pyfunction!(multimodal_evaluate, m)?)?;
    m.add_function(wrap_pyfunction!(multimodal_evaluate_generation, m)?)?;
    m.add_function(wrap_pyfunction!(agent_eval_evaluate, m)?)?;
    m.add_function(wrap_pyfunction!(production_monitor_tick, m)?)?;
    m.add_function(wrap_pyfunction!(safety_comprehensive_evaluation, m)?)?;
    m.add_function(wrap_pyfunction!(code_eval_evaluate, m)?)?;
    Ok(())
}
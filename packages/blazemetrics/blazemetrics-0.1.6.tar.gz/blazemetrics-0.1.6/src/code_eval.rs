use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Deserialize)]
struct CodeEvalInput {
    prompts: Vec<String>,
    generated_code: Vec<String>,
    reference_solutions: Vec<String>,
    metrics: Option<Vec<String>>,
    languages: Vec<String>,
    security_checks: bool,
    performance_analysis: bool,
}

#[derive(Serialize)]
struct CodeEvalResult {
    correctness: f64,
    efficiency: f64,
    security: f64,
    maintainability: f64,
    style_compliance: f64,
}

#[pyfunction]
pub fn code_eval_evaluate(input_json: &str) -> PyResult<String> {
    let input: CodeEvalInput = serde_json::from_str(input_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid input JSON: {}", e)))?;

    // correctness: compare generated code vs reference
    let mut correct = 0;
    for (gen, ref_sol) in input.generated_code.iter().zip(input.reference_solutions.iter()) {
        if gen.trim() == ref_sol.trim() {
            correct += 1;
        }
    }
    let correctness = correct as f64 / input.generated_code.len().max(1) as f64;

    // efficiency: average inverse length
    let efficiency = if input.performance_analysis {
        let avg_len: f64 = input.generated_code.iter().map(|c| c.len() as f64).sum::<f64>()
            / input.generated_code.len().max(1) as f64;
        1.0 / (1.0 + avg_len / 100.0)
    } else {
        0.0
    };

    // security: check for unsafe patterns
    let mut insecure_count = 0;
    let blacklist = vec!["eval", "exec", "unsafe", "os.system"];
    if input.security_checks {
        for code in &input.generated_code {
            let lower = code.to_lowercase();
            if blacklist.iter().any(|kw| lower.contains(kw)) {
                insecure_count += 1;
            }
        }
    }
    let security = 1.0 - (insecure_count as f64 / input.generated_code.len().max(1) as f64);

    // maintainability: heuristic = comment density
    let mut total_comments = 0;
    let mut total_lines = 0;
    for code in &input.generated_code {
        total_lines += code.lines().count();
        total_comments += code.lines().filter(|l| l.trim_start().starts_with("//") || l.trim_start().starts_with("#")).count();
    }
    let maintainability = total_comments as f64 / (total_lines.max(1) as f64);

    // style compliance: check indentation
    let mut style_issues = 0;
    let mut total = 0;
    for code in &input.generated_code {
        for line in code.lines() {
            total += 1;
            if line.starts_with("\t") {
                style_issues += 1;
            }
        }
    }
    let style_compliance = 1.0 - (style_issues as f64 / total.max(1) as f64);

    let result = CodeEvalResult {
        correctness,
        efficiency,
        security,
        maintainability,
        style_compliance,
    };

    Ok(serde_json::to_string(&result).unwrap())
}
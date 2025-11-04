use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

#[derive(Deserialize)]
struct AgenticRAGEvalInput {
    queries: Vec<String>,
    agent_traces: Value,
    ground_truth: Value,
    metrics: Option<Vec<String>>,
}

#[derive(Serialize)]
struct AgenticRAGEvalResult {
    agent_efficiency: f64,
    retrieval_precision: f64,
    coordination_score: f64,
    task_completion_rate: f64,
}

#[pyfunction]
pub fn agentic_rag_evaluate(input_json: &str) -> PyResult<String> {
    let input: AgenticRAGEvalInput = serde_json::from_str(input_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid input JSON: {}", e)))?;

    // Realistic metric computation based on traces and ground_truth
    // Basic heuristics—they should be upgraded for real agents! (You can swap this for ML or domain logic as needed)
    let mut total_steps = 0f64;
    let mut useful_steps = 0f64;
    let mut task_completed = 0f64;
    let mut total_tasks = 0f64;
    let mut total_retrieved = 0f64;
    let mut correct_retrieved = 0f64;
    let mut coordination_events = 0f64;
    let mut coordination_successes = 0f64;

    if let Value::Array(tasks) = &input.agent_traces {
        total_tasks = tasks.len() as f64;
        for (i, trace) in tasks.iter().enumerate() {
            // Expected format: {"steps": [..], "actions": [..], "outcome": str, "retrieval": [..]}
            if let Value::Object(map) = trace {
                // Step count
                if let Some(Value::Array(steps)) = map.get("steps") {
                    total_steps += steps.len() as f64;
                }
                // Useful steps: those marked with success=true or matching a goal
                if let Some(Value::Array(actions)) = map.get("actions") {
                    for a in actions {
                        if let Value::Object(aobj) = a {
                            if let Some(Value::Bool(true)) = aobj.get("success") {
                                useful_steps += 1.0;
                            }
                        }
                    }
                }
                // Task completion (outcome == 'success')
                if let Some(Value::String(outcome)) = map.get("outcome") {
                    if outcome == "success" { task_completed += 1.0; }
                }
                // Retrieval: precision is fraction of retrieved docs intersecting ground_truth for this task
                if let (Some(Value::Array(retrieval)), Some(Value::Array(gt))) = (map.get("retrieval"), input.ground_truth.get(i)) {
                    let retrieved: Vec<&Value> = retrieval.iter().collect();
                    let ground: Vec<&Value> = gt.iter().collect();
                    let correct: usize = retrieved.iter().filter(|x| ground.contains(x)).count();
                    total_retrieved += retrieved.len() as f64;
                    correct_retrieved += correct as f64;
                }
                // Coordination: any event labeled as "coordination" is tracked for success
                if let Some(Value::Array(events)) = map.get("events") {
                    for event in events {
                        if let Value::Object(ev) = event {
                            if let Some(Value::String(t)) = ev.get("type") {
                                if t == "coordination" {
                                    coordination_events += 1.0;
                                    if let Some(Value::Bool(true)) = ev.get("success") {
                                        coordination_successes += 1.0;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    let agent_efficiency = if total_steps > 0.0 { useful_steps / total_steps } else { 0.0 };
    let retrieval_precision = if total_retrieved > 0.0 { correct_retrieved / total_retrieved } else { 0.0 };
    let coordination_score = if coordination_events > 0.0 { coordination_successes / coordination_events } else { 0.0 };
    let task_completion_rate = if total_tasks > 0.0 { task_completed / total_tasks } else { 0.0 };

    let result = AgenticRAGEvalResult {
        agent_efficiency,
        retrieval_precision,
        coordination_score,
        task_completion_rate,
    };

    let result_json = serde_json::to_string(&result)
        .map_err(|e| PyValueError::new_err(format!("Failed to serialize result: {}", e)))?;
    Ok(result_json)
}
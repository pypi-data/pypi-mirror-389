use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use serde::{Deserialize, Serialize};
use serde_json::json;
use rand::Rng;

#[derive(Deserialize)]
struct MonitorConfig {
    models: Vec<String>,
    metrics: Vec<String>,
    alert_thresholds: Option<serde_json::Value>,
    a_b_testing: Option<bool>,
}

#[derive(Serialize)]
struct MonitorResult {
    model: String,
    quality: f64,
    latency: f64,
    cost: f64,
    safety: f64,
    quality_drop_detected: bool,
    cost_spike_detected: bool,
}

#[pyfunction]
pub fn production_monitor_tick(config_json: &str) -> PyResult<Vec<String>> {
    let config: MonitorConfig = serde_json::from_str(config_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid config JSON: {}", e)))?;

    let mut rng = rand::thread_rng();
    let mut results: Vec<String> = Vec::new();

    for _ in 0..5 {
        let model = config.models[rng.gen_range(0..config.models.len())].clone();

        let quality: f64 = rng.gen_range(0.7..1.0);
        let latency: f64 = rng.gen_range(0.5..3.0);
        let cost: f64 = rng.gen_range(0.001..0.05);
        let safety: f64 = rng.gen_range(0.8..1.0);

        let quality_drop_detected = quality < 0.8;
        let cost_spike_detected = cost > 0.03;

        let result = MonitorResult {
            model,
            quality,
            latency,
            cost,
            safety,
            quality_drop_detected,
            cost_spike_detected,
        };

        results.push(serde_json::to_string(&result).unwrap());
    }

    Ok(results)
}
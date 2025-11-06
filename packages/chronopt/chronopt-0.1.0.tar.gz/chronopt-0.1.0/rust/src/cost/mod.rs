use std::f64::consts::PI;

/// Trait for cost metrics applied to residuals between simulated and observed data.
pub trait CostMetric: Send + Sync {
    fn evaluate(&self, residuals: &[f64]) -> f64;
    fn name(&self) -> &'static str;
}

#[derive(Debug, Default)]
pub struct SumSquaredError;

impl CostMetric for SumSquaredError {
    fn evaluate(&self, residuals: &[f64]) -> f64 {
        residuals.iter().map(|r| r * r).sum()
    }

    fn name(&self) -> &'static str {
        "sse"
    }
}

#[derive(Debug, Default)]
pub struct RootMeanSquaredError;

impl CostMetric for RootMeanSquaredError {
    fn evaluate(&self, residuals: &[f64]) -> f64 {
        if residuals.is_empty() {
            return 0.0;
        }
        let mse: f64 = residuals.iter().map(|r| r * r).sum::<f64>() / residuals.len() as f64;
        mse.sqrt()
    }

    fn name(&self) -> &'static str {
        "rmse"
    }
}

#[derive(Debug, Clone, Copy)]
pub struct GaussianNll {
    variance: f64,
}

impl GaussianNll {
    pub fn new(variance: f64) -> Self {
        let variance = variance.max(f64::MIN_POSITIVE);
        Self { variance }
    }
}

impl Default for GaussianNll {
    fn default() -> Self {
        Self { variance: 1.0 }
    }
}

impl CostMetric for GaussianNll {
    fn evaluate(&self, residuals: &[f64]) -> f64 {
        if residuals.is_empty() {
            return 0.0;
        }

        let variance = self.variance;
        let sse: f64 = residuals.iter().map(|r| r * r).sum();
        let term_const = 0.5 * residuals.len() as f64 * (2.0 * PI * variance).ln();
        let term_quad = 0.5 * sse / variance;
        term_const + term_quad
    }

    fn name(&self) -> &'static str {
        "gaussian_nll"
    }
}

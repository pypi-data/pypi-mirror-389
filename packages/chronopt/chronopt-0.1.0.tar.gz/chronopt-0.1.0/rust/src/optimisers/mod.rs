use crate::problem::Problem;
use nalgebra::{DMatrix, DVector};
use rand::prelude::*;
use rand::rngs::StdRng;
use rand_distr::StandardNormal;
use std::cmp::Ordering;
use std::fmt;
use std::time::{Duration, Instant};

// Core behaviour shared by all optimisers
pub trait Optimiser {
    fn run(&self, problem: &Problem, initial: Vec<f64>) -> OptimisationResults;
}

pub trait WithMaxIter: Optimiser {
    fn set_max_iter(&mut self, max_iter: usize);

    fn with_max_iter(mut self, max_iter: usize) -> Self
    where
        Self: Sized,
    {
        self.set_max_iter(max_iter);
        self
    }
}

pub trait WithThreshold: Optimiser {
    fn set_threshold(&mut self, threshold: f64);

    fn with_threshold(mut self, threshold: f64) -> Self
    where
        Self: Sized,
    {
        self.set_threshold(threshold);
        self
    }
}

pub trait WithSigma0: Optimiser {
    fn set_sigma0(&mut self, sigma0: f64);

    fn with_sigma0(mut self, sigma0: f64) -> Self
    where
        Self: Sized,
    {
        self.set_sigma0(sigma0);
        self
    }
}

pub trait WithPatience: Optimiser {
    fn set_patience(&mut self, patience_seconds: f64);

    fn with_patience(mut self, patience_seconds: f64) -> Self
    where
        Self: Sized,
    {
        self.set_patience(patience_seconds);
        self
    }
}

enum InitialState {
    Ready {
        start: Vec<f64>,
        start_value: f64,
        nfev: usize,
    },
    Finished(OptimisationResults),
}

fn initialise_start(problem: &Problem, initial: Vec<f64>) -> InitialState {
    let start = if !initial.is_empty() {
        initial
    } else {
        vec![0.0; problem.dimension()]
    };

    let dim = start.len();
    let failed_time = Duration::try_from_secs_f64(0.0).expect("Failed to convert 0.0 to Duration");
    if dim == 0 {
        let value = match evaluate_point(problem, &start) {
            Ok(v) => v,
            Err(msg) => {
                let result = build_results(
                    &[EvaluatedPoint::new(Vec::new(), f64::NAN)],
                    0,
                    0,
                    failed_time,
                    TerminationReason::FunctionEvaluationFailed(msg),
                    None,
                );
                return InitialState::Finished(result);
            }
        };

        let result = build_results(
            &[EvaluatedPoint::new(start, value)],
            0,
            1,
            failed_time,
            TerminationReason::BothTolerancesReached,
            None,
        );
        return InitialState::Finished(result);
    }

    match evaluate_point(problem, &start) {
        Ok(value) => InitialState::Ready {
            start,
            start_value: value,
            nfev: 1,
        },
        Err(msg) => {
            let result = build_results(
                &[EvaluatedPoint::new(start, f64::NAN)],
                0,
                1,
                failed_time,
                TerminationReason::FunctionEvaluationFailed(msg),
                None,
            );
            InitialState::Finished(result)
        }
    }
}

#[derive(Debug, Clone)]
struct EvaluatedPoint {
    point: Vec<f64>,
    value: f64,
}

impl EvaluatedPoint {
    fn new(point: Vec<f64>, value: f64) -> Self {
        Self { point, value }
    }
}

fn evaluate_point(problem: &Problem, point: &[f64]) -> Result<f64, String> {
    problem.evaluate(point)
}

fn build_results(
    points: &[EvaluatedPoint],
    nit: usize,
    nfev: usize,
    time: Duration,
    reason: TerminationReason,
    covariance: Option<&DMatrix<f64>>,
) -> OptimisationResults {
    let mut ordered = points.to_vec();
    ordered.sort_by(|a, b| a.value.partial_cmp(&b.value).unwrap_or(Ordering::Equal));

    let best = ordered
        .first()
        .cloned()
        .unwrap_or_else(|| EvaluatedPoint::new(Vec::new(), f64::NAN));

    let final_simplex = ordered.iter().map(|v| v.point.clone()).collect();
    let final_simplex_values = ordered.iter().map(|v| v.value).collect();

    let covariance = covariance.map(|matrix| {
        (0..matrix.nrows())
            .map(|row| matrix.row(row).iter().copied().collect())
            .collect()
    });

    let success = matches!(
        reason,
        TerminationReason::FunctionToleranceReached
            | TerminationReason::ParameterToleranceReached
            | TerminationReason::BothTolerancesReached
    );

    let message = reason.to_string();

    OptimisationResults {
        x: best.point,
        fun: best.value,
        nit,
        nfev,
        time,
        success,
        message,
        termination_reason: reason,
        final_simplex,
        final_simplex_values,
        covariance,
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum TerminationReason {
    FunctionToleranceReached,
    ParameterToleranceReached,
    BothTolerancesReached,
    MaxIterationsReached,
    MaxFunctionEvaluationsReached,
    DegenerateSimplex,
    PatienceElapsed,
    FunctionEvaluationFailed(String),
}

impl fmt::Display for TerminationReason {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TerminationReason::FunctionToleranceReached => {
                write!(f, "Function tolerance met")
            }
            TerminationReason::ParameterToleranceReached => {
                write!(f, "Parameter tolerance met")
            }
            TerminationReason::BothTolerancesReached => {
                write!(f, "Function and parameter tolerances met")
            }
            TerminationReason::MaxIterationsReached => {
                write!(f, "Maximum iterations reached")
            }
            TerminationReason::MaxFunctionEvaluationsReached => {
                write!(f, "Maximum function evaluations reached")
            }
            TerminationReason::DegenerateSimplex => {
                write!(f, "Degenerate simplex encountered")
            }
            TerminationReason::PatienceElapsed => {
                write!(f, "Patience elapsed")
            }
            TerminationReason::FunctionEvaluationFailed(msg) => {
                write!(f, "Function evaluation failed: {}", msg)
            }
        }
    }
}

// Nelder-Mead optimiser
#[derive(Clone)]
pub struct NelderMead {
    max_iter: usize,
    threshold: f64,
    sigma0: f64,
    position_tolerance: f64,
    max_evaluations: Option<usize>,
    alpha: f64,
    gamma: f64,
    rho: f64,
    sigma: f64,
    patience: Option<Duration>,
}

impl NelderMead {
    pub fn new() -> Self {
        Self {
            max_iter: 1000,
            threshold: 1e-6,
            sigma0: 0.1,
            position_tolerance: 1e-6,
            max_evaluations: None,
            alpha: 1.0,
            gamma: 2.0,
            rho: 0.5,
            sigma: 0.5,
            patience: None,
        }
    }

    pub fn with_position_tolerance(mut self, tolerance: f64) -> Self {
        self.position_tolerance = tolerance.max(0.0);
        self
    }

    pub fn with_max_evaluations(mut self, max_evaluations: usize) -> Self {
        self.max_evaluations = Some(max_evaluations);
        self
    }

    pub fn with_coefficients(mut self, alpha: f64, gamma: f64, rho: f64, sigma: f64) -> Self {
        self.alpha = alpha;
        self.gamma = gamma;
        self.rho = rho;
        self.sigma = sigma;
        self
    }

    fn reached_max_evaluations(&self, evaluations: usize) -> bool {
        match self.max_evaluations {
            Some(limit) => evaluations >= limit,
            None => false,
        }
    }

    fn convergence_reason(&self, simplex: &[EvaluatedPoint]) -> Option<TerminationReason> {
        if simplex.is_empty() {
            return None;
        }

        let best = &simplex[0];
        let worst = simplex.last().unwrap();
        let fun_diff = (worst.value - best.value).abs();

        let mut max_dist: f64 = 0.0;
        for vertex in simplex.iter().skip(1) {
            let mut sum: f64 = 0.0;
            for (a, b) in vertex.point.iter().zip(best.point.iter()) {
                let diff = a - b;
                sum += diff * diff;
            }
            max_dist = max_dist.max(sum.sqrt());
        }

        let fun_converged = fun_diff <= self.threshold;
        let position_converged = max_dist <= self.position_tolerance;

        match (fun_converged, position_converged) {
            (true, true) => Some(TerminationReason::BothTolerancesReached),
            (true, false) => Some(TerminationReason::FunctionToleranceReached),
            (false, true) => Some(TerminationReason::ParameterToleranceReached),
            _ => None,
        }
    }

    fn centroid(simplex: &[EvaluatedPoint]) -> Vec<f64> {
        let dim = simplex[0].point.len();
        let mut centroid = vec![0.0; dim];
        let count = simplex.len() as f64;

        for vertex in simplex {
            for (c, val) in centroid.iter_mut().zip(&vertex.point) {
                *c += val;
            }
        }

        for c in centroid.iter_mut() {
            *c /= count;
        }

        centroid
    }

    pub fn run(&self, problem: &Problem, initial: Vec<f64>) -> OptimisationResults {
        let start_time = Instant::now();

        let (start, start_value, mut nfev) = match initialise_start(problem, initial) {
            InitialState::Finished(results) => return results,
            InitialState::Ready {
                start,
                start_value,
                nfev,
            } => (start, start_value, nfev),
        };

        let dim = start.len();

        let mut simplex = vec![EvaluatedPoint::new(start.clone(), start_value)];

        for i in 0..dim {
            if self.reached_max_evaluations(nfev) {
                return build_results(
                    &simplex,
                    0,
                    nfev,
                    start_time.elapsed(),
                    TerminationReason::MaxFunctionEvaluationsReached,
                    None,
                );
            }

            let mut point = start.clone();
            if point[i] != 0.0 {
                point[i] *= 1.0 + self.sigma0;
            } else {
                point[i] = self.sigma0;
            }

            if point
                .iter()
                .zip(simplex[0].point.iter())
                .all(|(a, b)| (*a - *b).abs() <= f64::EPSILON)
            {
                point[i] += self.sigma0;
            }

            let value = match evaluate_point(problem, &point) {
                Ok(v) => v,
                Err(msg) => {
                    return build_results(
                        &simplex,
                        0,
                        nfev,
                        start_time.elapsed(),
                        TerminationReason::FunctionEvaluationFailed(msg),
                        None,
                    )
                }
            };

            simplex.push(EvaluatedPoint::new(point, value));
            nfev += 1;
        }

        if simplex.len() != dim + 1 {
            return build_results(
                &simplex,
                0,
                nfev,
                start_time.elapsed(),
                TerminationReason::DegenerateSimplex,
                None,
            );
        }

        let mut nit = 0usize;
        if let Some(patience) = self.patience {
            if start_time.elapsed() >= patience {
                return build_results(
                    &simplex,
                    nit,
                    nfev,
                    start_time.elapsed(),
                    TerminationReason::PatienceElapsed,
                    None,
                );
            }
        }
        let mut termination = TerminationReason::MaxIterationsReached;

        loop {
            if let Some(patience) = self.patience {
                if start_time.elapsed() >= patience {
                    termination = TerminationReason::PatienceElapsed;
                    break;
                }
            }

            simplex.sort_by(|a, b| a.value.partial_cmp(&b.value).unwrap_or(Ordering::Equal));

            if let Some(reason) = self.convergence_reason(&simplex) {
                termination = reason;
                break;
            }

            if nit >= self.max_iter {
                termination = TerminationReason::MaxIterationsReached;
                break;
            }

            if self.reached_max_evaluations(nfev) {
                termination = TerminationReason::MaxFunctionEvaluationsReached;
                break;
            }

            nit += 1;

            let worst_index = simplex.len() - 1;
            let centroid = Self::centroid(&simplex[..worst_index]);
            let worst = simplex[worst_index].clone();

            let reflected_point: Vec<f64> = centroid
                .iter()
                .zip(&worst.point)
                .map(|(c, w)| c + self.alpha * (c - w))
                .collect();

            let reflected_value = match evaluate_point(problem, &reflected_point) {
                Ok(v) => v,
                Err(msg) => {
                    termination = TerminationReason::FunctionEvaluationFailed(msg);
                    simplex[worst_index] = EvaluatedPoint::new(reflected_point, f64::NAN);
                    nfev += 1;
                    break;
                }
            };

            nfev += 1;

            if reflected_value < simplex[0].value {
                if self.reached_max_evaluations(nfev) {
                    termination = TerminationReason::MaxFunctionEvaluationsReached;
                    simplex[worst_index] = EvaluatedPoint::new(reflected_point, reflected_value);
                    break;
                }

                let expanded_point: Vec<f64> = centroid
                    .iter()
                    .zip(&reflected_point)
                    .map(|(c, r)| c + self.gamma * (r - c))
                    .collect();

                let expanded_value = match evaluate_point(problem, &expanded_point) {
                    Ok(v) => v,
                    Err(msg) => {
                        termination = TerminationReason::FunctionEvaluationFailed(msg);
                        simplex[worst_index] =
                            EvaluatedPoint::new(reflected_point, reflected_value);
                        nfev += 1;
                        break;
                    }
                };

                nfev += 1;

                if expanded_value < reflected_value {
                    simplex[worst_index] = EvaluatedPoint::new(expanded_point, expanded_value);
                } else {
                    simplex[worst_index] = EvaluatedPoint::new(reflected_point, reflected_value);
                }
                continue;
            }

            if reflected_value < simplex[worst_index - 1].value {
                simplex[worst_index] = EvaluatedPoint::new(reflected_point, reflected_value);
                continue;
            }

            let (contract_point, contract_value) = if reflected_value < worst.value {
                // Outside contraction
                let point: Vec<f64> = centroid
                    .iter()
                    .zip(&reflected_point)
                    .map(|(c, r)| c + self.rho * (r - c))
                    .collect();

                if self.reached_max_evaluations(nfev) {
                    termination = TerminationReason::MaxFunctionEvaluationsReached;
                    simplex[worst_index] = EvaluatedPoint::new(reflected_point, reflected_value);
                    break;
                }

                let value = match evaluate_point(problem, &point) {
                    Ok(v) => v,
                    Err(msg) => {
                        termination = TerminationReason::FunctionEvaluationFailed(msg);
                        simplex[worst_index] =
                            EvaluatedPoint::new(reflected_point, reflected_value);
                        nfev += 1;
                        break;
                    }
                };

                nfev += 1;
                (point, value)
            } else {
                // Inside contraction
                let point: Vec<f64> = centroid
                    .iter()
                    .zip(&worst.point)
                    .map(|(c, w)| c + self.rho * (w - c))
                    .collect();

                if self.reached_max_evaluations(nfev) {
                    termination = TerminationReason::MaxFunctionEvaluationsReached;
                    simplex[worst_index] = EvaluatedPoint::new(reflected_point, reflected_value);
                    break;
                }

                let value = match evaluate_point(problem, &point) {
                    Ok(v) => v,
                    Err(msg) => {
                        termination = TerminationReason::FunctionEvaluationFailed(msg);
                        simplex[worst_index] =
                            EvaluatedPoint::new(reflected_point, reflected_value);
                        nfev += 1;
                        break;
                    }
                };

                nfev += 1;
                (point, value)
            };

            if termination != TerminationReason::MaxIterationsReached
                && matches!(termination, TerminationReason::FunctionEvaluationFailed(_))
            {
                break;
            }

            if contract_value < worst.value {
                simplex[worst_index] = EvaluatedPoint::new(contract_point, contract_value);
                continue;
            }

            // Shrink
            let best_point = simplex[0].point.clone();
            for item in simplex.iter_mut().skip(1) {
                if self.reached_max_evaluations(nfev) {
                    termination = TerminationReason::MaxFunctionEvaluationsReached;
                    break;
                }

                let new_point: Vec<f64> = best_point
                    .iter()
                    .zip(item.point.iter())
                    .map(|(b, x)| b + self.sigma * (x - b))
                    .collect();

                match evaluate_point(problem, &new_point) {
                    Ok(val) => {
                        *item = EvaluatedPoint::new(new_point, val);
                        nfev += 1;
                    }
                    Err(msg) => {
                        termination = TerminationReason::FunctionEvaluationFailed(msg);
                        *item = EvaluatedPoint::new(new_point, f64::NAN);
                        nfev += 1;
                        break;
                    }
                }
            }

            if matches!(
                termination,
                TerminationReason::MaxFunctionEvaluationsReached
                    | TerminationReason::FunctionEvaluationFailed(_)
            ) {
                break;
            }
        }

        build_results(&simplex, nit, nfev, start_time.elapsed(), termination, None)
    }
}

impl Optimiser for NelderMead {
    fn run(&self, problem: &Problem, initial: Vec<f64>) -> OptimisationResults {
        self.run(problem, initial)
    }
}

impl WithMaxIter for NelderMead {
    fn set_max_iter(&mut self, max_iter: usize) {
        self.max_iter = max_iter;
    }
}

impl WithThreshold for NelderMead {
    fn set_threshold(&mut self, threshold: f64) {
        self.threshold = threshold;
    }
}

impl WithSigma0 for NelderMead {
    fn set_sigma0(&mut self, sigma0: f64) {
        self.sigma0 = sigma0;
    }
}

impl WithPatience for NelderMead {
    fn set_patience(&mut self, patience_seconds: f64) {
        if patience_seconds.is_finite() && patience_seconds > 0.0 {
            self.patience = Some(Duration::from_secs_f64(patience_seconds));
        } else {
            self.patience = None;
        }
    }
}

impl Default for NelderMead {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone)]
pub struct CMAES {
    max_iter: usize,
    threshold: f64,
    sigma0: f64,
    patience: Option<Duration>,
    population_size: Option<usize>,
    seed: Option<u64>,
}

impl CMAES {
    pub fn new() -> Self {
        Self {
            max_iter: 1000,
            threshold: 1e-6,
            sigma0: 0.5,
            patience: None,
            population_size: None,
            seed: None,
        }
    }

    pub fn with_population_size(mut self, population_size: usize) -> Self {
        if population_size > 1 {
            self.population_size = Some(population_size);
        }
        self
    }

    pub fn with_seed(mut self, seed: u64) -> Self {
        self.seed = Some(seed);
        self
    }

    fn population_size(&self, dim: usize) -> usize {
        if let Some(size) = self.population_size {
            size.max(2)
        } else if dim > 0 {
            let suggested = (4.0 + (3.0 * (dim as f64).ln())).floor() as usize;
            suggested.max(4).max(2 * dim)
        } else {
            4
        }
    }

    pub fn run(&self, problem: &Problem, initial: Vec<f64>) -> OptimisationResults {
        let start_time = Instant::now();

        let (start, start_value, mut nfev) = match initialise_start(problem, initial) {
            InitialState::Finished(results) => return results,
            InitialState::Ready {
                start,
                start_value,
                nfev,
            } => (start, start_value, nfev),
        };

        let dim = start.len();
        if dim == 0 {
            return build_results(
                &[EvaluatedPoint::new(start, start_value)],
                0,
                nfev,
                start_time.elapsed(),
                TerminationReason::BothTolerancesReached,
                None,
            );
        }

        let dim_f = dim as f64;

        let mut mean = DVector::from_vec(start.clone());
        let mut sigma = self.sigma0.max(1e-12);
        let mut cov = DMatrix::identity(dim, dim);
        let mut p_sigma = DVector::zeros(dim);
        let mut p_c = DVector::zeros(dim);
        let mut eigenvectors = DMatrix::identity(dim, dim);
        let mut sqrt_eigenvalues = DVector::from_element(dim, 1.0);
        let mut inv_sqrt_cov = DMatrix::identity(dim, dim);

        let mut rng: StdRng = match self.seed {
            Some(seed) => StdRng::seed_from_u64(seed),
            None => StdRng::from_entropy(),
        };

        let lambda = self.population_size(dim);
        let mu = (lambda / 2).max(1);
        let mut weights: Vec<f64> = (0..mu).map(|i| (mu - i) as f64).collect();
        let weight_sum: f64 = weights.iter().sum();
        for w in &mut weights {
            *w /= weight_sum;
        }
        let mu_eff = 1.0 / weights.iter().map(|w| w * w).sum::<f64>();

        let c_sigma = (mu_eff + 2.0) / (dim_f + mu_eff + 5.0);
        let d_sigma = 1.0 + c_sigma + 2.0 * ((mu_eff - 1.0) / (dim_f + 1.0)).max(0.0).sqrt();
        let c_c = (4.0 + mu_eff / dim_f) / (dim_f + 4.0 + 2.0 * mu_eff / dim_f);
        let c1 = 2.0 / ((dim_f + 1.3).powi(2) + mu_eff);
        let c_mu = ((1.0 - c1)
            .min(2.0 * (mu_eff - 2.0 + 1.0 / mu_eff) / ((dim_f + 2.0).powi(2) + mu_eff)))
        .max(0.0);
        let chi_n = dim_f.sqrt() * (1.0 - 1.0 / (4.0 * dim_f) + 1.0 / (21.0 * dim_f.powi(2)));

        let mut nit = 0usize;
        let mut termination = TerminationReason::MaxIterationsReached;
        let mut best_point = EvaluatedPoint::new(start.clone(), start_value);
        let mut final_population = vec![best_point.clone()];

        while nit < self.max_iter {
            if let Some(patience) = self.patience {
                if start_time.elapsed() >= patience {
                    termination = TerminationReason::PatienceElapsed;
                    break;
                }
            }

            if dim > 0 {
                let sym = (&cov + cov.transpose()) * 0.5;
                let eig = sym.symmetric_eigen();
                eigenvectors = eig.eigenvectors;
                sqrt_eigenvalues = eig.eigenvalues.map(|val: f64| val.max(1e-30).sqrt());

                let inv_diag = sqrt_eigenvalues.map(|val| {
                    if val > 0.0 {
                        (1.0 / val).min(1e12_f64)
                    } else {
                        1e12
                    }
                });
                inv_sqrt_cov =
                    &eigenvectors * DMatrix::from_diagonal(&inv_diag) * eigenvectors.transpose();
            }

            let step_matrix = DMatrix::from_diagonal(&sqrt_eigenvalues);

            let mut sampled_points: Vec<Vec<f64>> = Vec::with_capacity(lambda);
            let mut sampled_steps: Vec<DVector<f64>> = Vec::with_capacity(lambda);

            for _ in 0..lambda {
                let z = DVector::from_iterator(
                    dim,
                    (0..dim).map(|_| rng.sample::<f64, _>(StandardNormal)),
                );

                let step = &eigenvectors * (&step_matrix * &z);

                let candidate_vec = mean.clone() + step * sigma;
                let candidate: Vec<f64> = candidate_vec.iter().cloned().collect();

                sampled_points.push(candidate);
                sampled_steps.push(z);
            }

            let evaluations = problem.evaluate_population(&sampled_points);
            nfev += evaluations.len();

            let mut population: Vec<(EvaluatedPoint, DVector<f64>)> = Vec::with_capacity(lambda);
            for ((candidate, z), result) in sampled_points
                .into_iter()
                .zip(sampled_steps.into_iter())
                .zip(evaluations.into_iter())
            {
                let (candidate, z) = (candidate, z);
                match result {
                    Ok(value) => {
                        population.push((EvaluatedPoint::new(candidate, value), z));
                    }
                    Err(msg) => {
                        let mut final_points: Vec<EvaluatedPoint> =
                            population.iter().map(|(pt, _)| pt.clone()).collect();
                        final_points.push(EvaluatedPoint::new(candidate, f64::NAN));
                        return build_results(
                            &final_points,
                            nit,
                            nfev,
                            start_time.elapsed(),
                            TerminationReason::FunctionEvaluationFailed(msg),
                            Some(&cov),
                        );
                    }
                }
            }

            population.sort_by(|a, b| a.0.value.partial_cmp(&b.0.value).unwrap_or(Ordering::Equal));

            let mut current_points: Vec<EvaluatedPoint> =
                population.iter().map(|(pt, _)| pt.clone()).collect();

            if let Some(best) = current_points.first() {
                if best.value < best_point.value {
                    best_point = best.clone();
                }
            }

            if !current_points.iter().any(|pt| pt.point == best_point.point) {
                current_points.push(best_point.clone());
            }

            let fun_diff = if current_points.len() > 1 {
                let mut sorted = current_points.clone();
                sorted.sort_by(|a, b| a.value.partial_cmp(&b.value).unwrap_or(Ordering::Equal));
                let best = &sorted[0];
                let worst = &sorted[sorted.len() - 1];
                (worst.value - best.value).abs()
            } else {
                0.0
            };

            let old_mean = mean.clone();
            let mut new_mean = DVector::zeros(dim);
            for i in 0..mu.min(population.len()) {
                let weight = weights[i];
                let candidate_vec = DVector::from_column_slice(&population[i].0.point);
                new_mean += candidate_vec.clone() * weight;
            }
            mean = new_mean;

            let mean_shift = &mean - &old_mean;

            let norm_factor = (c_sigma * (2.0 - c_sigma) * mu_eff).sqrt();
            let mut mean_shift_sigma = mean_shift.clone();
            if sigma > 0.0 {
                mean_shift_sigma /= sigma;
            }
            let delta = &inv_sqrt_cov * mean_shift_sigma.clone();
            let delta_scaled = delta * norm_factor;
            p_sigma = p_sigma * (1.0 - c_sigma) + delta_scaled;

            let norm_p_sigma = p_sigma.norm();
            let exponent = 2.0 * ((nit + 1) as f64);
            let factor = (1.0 - (1.0 - c_sigma).powf(exponent)).max(1e-12).sqrt();
            let h_sigma_threshold = (1.4 + 2.0 / (dim_f + 1.0)) * chi_n;
            let h_sigma = if norm_p_sigma / factor < h_sigma_threshold {
                1.0
            } else {
                0.0
            };

            let pc_factor = (c_c * (2.0 - c_c) * mu_eff).sqrt();
            let mean_shift_scaled = if sigma > 0.0 {
                mean_shift.clone() * (h_sigma * pc_factor / sigma.max(1e-12))
            } else {
                DVector::zeros(dim)
            };
            p_c = p_c * (1.0 - c_c) + mean_shift_scaled;

            cov = cov * (1.0 - c1 - c_mu) + (p_c.clone() * p_c.transpose()) * c1;

            for i in 0..mu.min(population.len()) {
                let weight = weights[i];
                let candidate_vec = DVector::from_column_slice(&population[i].0.point);
                let y = (candidate_vec - &old_mean) / sigma.max(1e-12);
                cov += (&y * y.transpose()) * (c_mu * weight);
            }

            if dim > 0 {
                cov = (&cov + cov.transpose()) * 0.5;
            }

            sigma *= (c_sigma / d_sigma * (norm_p_sigma / chi_n - 1.0)).exp();
            sigma = sigma.max(1e-18);

            nit += 1;
            final_population = current_points;

            let position_converged = mean_shift.norm() <= self.threshold;
            let fun_converged = fun_diff <= self.threshold;
            if fun_converged && position_converged {
                termination = TerminationReason::BothTolerancesReached;
                break;
            } else if fun_converged {
                termination = TerminationReason::FunctionToleranceReached;
                break;
            } else if position_converged {
                termination = TerminationReason::ParameterToleranceReached;
                break;
            }

            if let Some(patience) = self.patience {
                if start_time.elapsed() >= patience {
                    termination = TerminationReason::PatienceElapsed;
                    break;
                }
            }
        }

        build_results(
            &final_population,
            nit,
            nfev,
            start_time.elapsed(),
            termination,
            Some(&cov),
        )
    }
}

impl Optimiser for CMAES {
    fn run(&self, problem: &Problem, initial: Vec<f64>) -> OptimisationResults {
        self.run(problem, initial)
    }
}

impl WithMaxIter for CMAES {
    fn set_max_iter(&mut self, max_iter: usize) {
        self.max_iter = max_iter;
    }
}

impl WithThreshold for CMAES {
    fn set_threshold(&mut self, threshold: f64) {
        self.threshold = threshold;
    }
}

impl WithSigma0 for CMAES {
    fn set_sigma0(&mut self, sigma0: f64) {
        self.sigma0 = sigma0.max(1e-12);
    }
}

impl WithPatience for CMAES {
    fn set_patience(&mut self, patience_seconds: f64) {
        if patience_seconds.is_finite() && patience_seconds > 0.0 {
            self.patience = Some(Duration::from_secs_f64(patience_seconds));
        } else {
            self.patience = None;
        }
    }
}

impl Default for CMAES {
    fn default() -> Self {
        Self::new()
    }
}

// Results object
#[derive(Debug, Clone)]
pub struct OptimisationResults {
    pub x: Vec<f64>,
    pub fun: f64,
    pub nit: usize,
    pub nfev: usize,
    pub time: Duration,
    pub success: bool,
    pub message: String,
    pub termination_reason: TerminationReason,
    pub final_simplex: Vec<Vec<f64>>,
    pub final_simplex_values: Vec<f64>,
    pub covariance: Option<Vec<Vec<f64>>>,
}

impl OptimisationResults {
    fn __repr__(&self) -> String {
        format!(
            "OptimisationResults(x={:?}, fun={:.6}, nit={}, nfev={}, time={:?}, success={}, reason={})",
            self.x, self.fun, self.nit, self.nfev, self.time, self.success, self.message
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::problem::Builder;

    #[test]
    fn nelder_mead_minimises_quadratic() {
        let problem = Builder::new()
            .with_objective(|x: &[f64]| {
                let x0 = x[0] - 1.5;
                let x1 = x[1] + 0.5;
                x0 * x0 + x1 * x1
            })
            .build()
            .unwrap();

        let optimiser = NelderMead::new()
            .with_max_iter(400)
            .with_threshold(1e-10)
            .with_sigma0(0.6)
            .with_position_tolerance(1e-8);

        let result = optimiser.run(&problem, vec![5.0, -4.0]);

        assert!(result.success, "Expected success: {}", result.message);
        assert!((result.x[0] - 1.5).abs() < 1e-5);
        assert!((result.x[1] + 0.5).abs() < 1e-5);
        assert!(result.fun < 1e-9, "Final value too large: {}", result.fun);
        assert!(result.nit > 0);
        assert!(result.nfev >= result.nit + 1);
    }

    #[test]
    fn nelder_mead_respects_max_iterations() {
        let problem = Builder::new()
            .with_objective(|x: &[f64]| x.iter().map(|xi| xi * xi).sum())
            .build()
            .unwrap();

        let optimiser = NelderMead::new().with_max_iter(1).with_sigma0(1.0);
        let result = optimiser.run(&problem, vec![10.0, -10.0]);

        assert_eq!(
            result.termination_reason,
            TerminationReason::MaxIterationsReached
        );
        assert!(!result.success);
        assert!(result.nit <= 1);
    }

    #[test]
    fn nelder_mead_respects_max_function_evaluations() {
        let problem = Builder::new()
            .with_objective(|x: &[f64]| x.iter().map(|xi| xi * xi).sum())
            .build()
            .unwrap();

        let optimiser = NelderMead::new()
            .with_max_evaluations(2)
            .with_sigma0(0.5)
            .with_max_iter(500);

        let result = optimiser.run(&problem, vec![2.0, 2.0]);

        assert_eq!(
            result.termination_reason,
            TerminationReason::MaxFunctionEvaluationsReached
        );
        assert!(!result.success);
        assert!(result.nfev <= 2);
    }

    #[test]
    fn nelder_mead_respects_patience() {
        let problem = Builder::new()
            .with_objective(|x: &[f64]| {
                std::thread::sleep(Duration::from_millis(5));
                x.iter().map(|xi| xi * xi).sum()
            })
            .build()
            .unwrap();

        let optimiser = NelderMead::new().with_sigma0(0.5).with_patience(0.01);

        let result = optimiser.run(&problem, vec![5.0, -5.0]);

        assert_eq!(
            result.termination_reason,
            TerminationReason::PatienceElapsed
        );
        assert!(!result.success);
    }

    #[test]
    fn cmaes_minimises_quadratic() {
        let problem = Builder::new()
            .with_objective(|x: &[f64]| {
                let x0 = x[0] - 1.5;
                let x1 = x[1] + 0.5;
                x0 * x0 + x1 * x1
            })
            .build()
            .unwrap();

        let optimiser = CMAES::new()
            .with_max_iter(400)
            .with_threshold(1e-10)
            .with_sigma0(0.6)
            .with_patience(5.0)
            .with_seed(42);

        let result = optimiser.run(&problem, vec![5.0, -4.0]);

        assert!(result.success, "Expected success: {}", result.message);
        assert!((result.x[0] - 1.5).abs() < 1e-4);
        assert!((result.x[1] + 0.5).abs() < 1e-4);
        assert!(result.fun < 1e-8, "Final value too large: {}", result.fun);
        assert!(result.nit > 0);
        assert!(result.nfev >= result.nit + 1);
    }

    #[test]
    fn cmaes_respects_max_iterations() {
        let problem = Builder::new()
            .with_objective(|x: &[f64]| x.iter().map(|xi| xi * xi).sum())
            .build()
            .unwrap();

        let optimiser = CMAES::new().with_max_iter(1).with_sigma0(0.5).with_seed(7);
        let result = optimiser.run(&problem, vec![10.0, -10.0]);

        assert_eq!(
            result.termination_reason,
            TerminationReason::MaxIterationsReached
        );
        assert!(!result.success);
        assert!(result.nit <= 1);
    }

    #[test]
    fn cmaes_respects_patience() {
        let problem = Builder::new()
            .with_objective(|x: &[f64]| {
                std::thread::sleep(Duration::from_millis(5));
                x.iter().map(|xi| xi * xi).sum()
            })
            .build()
            .unwrap();

        let optimiser = CMAES::new()
            .with_sigma0(0.5)
            .with_patience(0.01)
            .with_seed(5);

        let result = optimiser.run(&problem, vec![5.0, -5.0]);

        assert_eq!(
            result.termination_reason,
            TerminationReason::PatienceElapsed
        );
        assert!(!result.success);
    }
}


"""

(PSM)(DID)(RDD)
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings('ignore')


class PSMMatchResult(BaseModel):
    """"""
    matched_pairs: List[Tuple[int, int]] = Field(description="")
    treatment_effect: float = Field(description="")
    standard_error: float = Field(description="")
    t_statistic: float = Field(description="t")
    p_value: float = Field(description="p")
    matched_sample_size: int = Field(description="")
    balance_metrics: Dict[str, float] = Field(description="")


class DIDResult(BaseModel):
    """"""
    did_estimate: float = Field(description="DID")
    standard_error: float = Field(description="")
    t_statistic: float = Field(description="t")
    p_value: float = Field(description="p")
    pre_treatment_diff: float = Field(description="")
    post_treatment_diff: float = Field(description="")
    time_trend: float = Field(description="")
    parallel_trend_test: Dict[str, float] = Field(description="")


class RDDResult(BaseModel):
    """"""
    treatment_effect: float = Field(description="")
    standard_error: float = Field(description="")
    t_statistic: float = Field(description="t")
    p_value: float = Field(description="p")
    bandwidth: float = Field(description="")
    cutoff: float = Field(description="")
    polynomial_order: int = Field(description="")
    density_test: Dict[str, float] = Field(description="")


class QuantileRegressionResult(BaseModel):
    """"""
    quantile: float = Field(description="")
    coefficients: Dict[str, Dict[str, float]] = Field(description="")
    pseudo_rsquared: float = Field(description="R²")
    n_obs: int = Field(description="")


class SurvivalAnalysisResult(BaseModel):
    """"""
    hazard_ratios: Dict[str, float] = Field(description="")
    coefficients: Dict[str, Dict[str, float]] = Field(description="")
    baseline_survival: List[float] = Field(description="")
    median_survival_time: float = Field(description="")
    log_likelihood: float = Field(description="")


def propensity_score_matching(
    treatment: List[int],
    covariates: List[List[float]],
    outcome: List[float],
    feature_names: Optional[List[str]] = None,
    method: str = "nearest",
    caliper: float = 0.2
) -> PSMMatchResult:
    """
    (PSM)
    
     
    
    
     
    1. Logistic
    2. 
    3. 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        treatment: 0=1=
        covariates: 
        outcome: 
        feature_names: 
        method: "nearest", "radius", "kernel"
        caliper: 
    
    Returns:
        PSMMatchResult: 
    """
    # 
    if not treatment or not covariates or not outcome:
        raise ValueError("")
    
    if len(treatment) != len(covariates) or len(treatment) != len(outcome):
        raise ValueError("")
    
    # 
    X = np.array(covariates)
    y_treatment = np.array(treatment)
    y_outcome = np.array(outcome)
    
    # 
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(X.shape[1])]
    elif len(feature_names) != X.shape[1]:
        raise ValueError(f"({len(feature_names)})({X.shape[1]})")
    
    # 
    try:
        ps_model = LogisticRegression(random_state=42)
        ps_model.fit(X, y_treatment)
        propensity_scores = ps_model.predict_proba(X)[:, 1]
    except Exception as e:
        raise ValueError(f": {str(e)}")
    
    # 
    treatment_indices = np.where(y_treatment == 1)[0]
    control_indices = np.where(y_treatment == 0)[0]
    
    matched_pairs = []
    matched_treatment_outcomes = []
    matched_control_outcomes = []
    
    for treat_idx in treatment_indices:
        treat_ps = propensity_scores[treat_idx]
        
        # 
        control_dists = []
        for control_idx in control_indices:
            control_ps = propensity_scores[control_idx]
            dist = abs(treat_ps - control_ps)
            if dist <= caliper:
                control_dists.append((control_idx, dist))
        
        if control_dists:
            # 
            best_match = min(control_dists, key=lambda x: x[1])
            matched_pairs.append((treat_idx, best_match[0]))
            matched_treatment_outcomes.append(y_outcome[treat_idx])
            matched_control_outcomes.append(y_outcome[best_match[0]])
    
    if not matched_pairs:
        raise ValueError("(caliper)")
    
    # 
    treatment_effect = np.mean(matched_treatment_outcomes) - np.mean(matched_control_outcomes)
    
    # 
    n_matched = len(matched_pairs)
    se = np.std([matched_treatment_outcomes[i] - matched_control_outcomes[i] 
                for i in range(n_matched)]) / np.sqrt(n_matched)
    
    # tp
    t_stat = treatment_effect / se if se > 0 else 0
    from scipy import stats
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n_matched - 1))
    
    # 
    balance_metrics = {}
    for i, feature_name in enumerate(feature_names):
        treat_vals = [X[pair[0], i] for pair in matched_pairs]
        control_vals = [X[pair[1], i] for pair in matched_pairs]
        balance_metrics[feature_name] = abs(np.mean(treat_vals) - np.mean(control_vals))
    
    return PSMMatchResult(
        matched_pairs=matched_pairs,
        treatment_effect=float(treatment_effect),
        standard_error=float(se),
        t_statistic=float(t_stat),
        p_value=float(p_val),
        matched_sample_size=n_matched,
        balance_metrics=balance_metrics
    )


def difference_in_differences(
    treatment: List[int],
    time_period: List[int],
    outcome: List[float],
    covariates: Optional[List[List[float]]] = None
) -> DIDResult:
    """
    (DID)
    
     
    
    
     
    DID = (-) - (-)
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        treatment: 0=1=
        time_period: 0=1=
        outcome: 
        covariates: 
    
    Returns:
        DIDResult: 
    """
    # 
    if not treatment or not time_period or not outcome:
        raise ValueError("")
    
    if len(treatment) != len(time_period) or len(treatment) != len(outcome):
        raise ValueError("")
    
    # 
    y_outcome = np.array(outcome)
    y_treatment = np.array(treatment)
    y_time = np.array(time_period)
    
    # DID
    did_data = []
    for i in range(len(y_treatment)):
        row = [
            y_treatment[i],           # 
            y_time[i],                # 
            y_treatment[i] * y_time[i]  # DID
        ]
        # 
        if covariates is not None:
            row.extend(covariates[i])
        did_data.append(row)
    
    # 
    X = sm.add_constant(did_data)
    
    # DID
    try:
        model = sm.OLS(y_outcome, X)
        fitted_model = model.fit()
    except Exception as e:
        raise ValueError(f"DID: {str(e)}")
    
    # DID
    did_coef = fitted_model.params[3]  # +
    did_se = fitted_model.bse[3]
    did_t = fitted_model.tvalues[3]
    did_p = fitted_model.pvalues[3]
    
    # 
    treat_pre = np.mean(y_outcome[(y_treatment == 1) & (y_time == 0)])
    treat_post = np.mean(y_outcome[(y_treatment == 1) & (y_time == 1)])
    control_pre = np.mean(y_outcome[(y_treatment == 0) & (y_time == 0)])
    control_post = np.mean(y_outcome[(y_treatment == 0) & (y_time == 1)])
    
    pre_diff = treat_pre - control_pre
    post_diff = treat_post - control_post
    time_trend = control_post - control_pre
    
    # 
    parallel_test = {
        "pre_treatment_diff": float(pre_diff),
        "post_treatment_diff": float(post_diff),
        "time_trend_control": float(time_trend)
    }
    
    return DIDResult(
        did_estimate=float(did_coef),
        standard_error=float(did_se),
        t_statistic=float(did_t),
        p_value=float(did_p),
        pre_treatment_diff=float(pre_diff),
        post_treatment_diff=float(post_diff),
        time_trend=float(time_trend),
        parallel_trend_test=parallel_test
    )


def regression_discontinuity(
    running_variable: List[float],
    outcome: List[float],
    cutoff: float,
    bandwidth: Optional[float] = None,
    polynomial_order: int = 1
) -> RDDResult:
    """
    (RDD)
    
     
    
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        running_variable: 
        outcome: 
        cutoff: 
        bandwidth: None
        polynomial_order: 
    
    Returns:
        RDDResult: 
    """
    # 
    if not running_variable or not outcome:
        raise ValueError("")
    
    if len(running_variable) != len(outcome):
        raise ValueError("")
    
    # 
    X_run = np.array(running_variable)
    y_outcome = np.array(outcome)
    
    # 
    if bandwidth is None:
        bandwidth = 0.5 * np.std(X_run)
    
    # 
    mask = (X_run >= cutoff - bandwidth) & (X_run <= cutoff + bandwidth)
    if np.sum(mask) < 10:
        raise ValueError(f"({np.sum(mask)})")
    
    X_local = X_run[mask]
    y_local = y_outcome[mask]
    
    # 
    treatment = (X_local >= cutoff).astype(int)
    
    # 
    X_poly = []
    for x in X_local:
        row = [1]  # 
        for order in range(1, polynomial_order + 1):
            row.append((x - cutoff) ** order)
        X_poly.append(row)
    
    X_poly = np.array(X_poly)
    
    # 
    X_rdd = np.column_stack([X_poly, treatment])
    
    # RDD
    try:
        model = sm.OLS(y_local, X_rdd)
        fitted_model = model.fit()
    except Exception as e:
        raise ValueError(f"RDD: {str(e)}")
    
    # 
    treatment_effect = fitted_model.params[-1]
    treatment_se = fitted_model.bse[-1]
    treatment_t = fitted_model.tvalues[-1]
    treatment_p = fitted_model.pvalues[-1]
    
    # 
    left_density = np.sum(X_local < cutoff) / len(X_local)
    right_density = np.sum(X_local >= cutoff) / len(X_local)
    density_ratio = left_density / right_density if right_density > 0 else float('inf')
    
    density_test = {
        "left_density": float(left_density),
        "right_density": float(right_density),
        "density_ratio": float(density_ratio)
    }
    
    return RDDResult(
        treatment_effect=float(treatment_effect),
        standard_error=float(treatment_se),
        t_statistic=float(treatment_t),
        p_value=float(treatment_p),
        bandwidth=float(bandwidth),
        cutoff=float(cutoff),
        polynomial_order=polynomial_order,
        density_test=density_test
    )


def quantile_regression(
    y_data: List[float],
    x_data: List[List[float]],
    quantile: float = 0.5,
    feature_names: Optional[List[str]] = None
) -> QuantileRegressionResult:
    """
    
    
     
    
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        y_data: 
        x_data: 
        quantile: 0-1
        feature_names: 
    
    Returns:
        QuantileRegressionResult: 
    """
    # 
    if not y_data or not x_data:
        raise ValueError("")
    
    if len(y_data) != len(x_data):
        raise ValueError(f": y_data={len(y_data)}, x_data={len(x_data)}")
    
    if not 0 < quantile < 1:
        raise ValueError("01")
    
    # 
    X = np.array(x_data)
    y = np.array(y_data)
    
    # 
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(X.shape[1])]
    elif len(feature_names) != X.shape[1]:
        raise ValueError(f"({len(feature_names)})({X.shape[1]})")
    
    # 
    X_with_const = sm.add_constant(X)
    full_feature_names = ["const"] + feature_names
    
    # 
    try:
        model = sm.QuantReg(y, X_with_const)
        fitted_model = model.fit(q=quantile)
    except Exception as e:
       
        raise ValueError(f": {str(e)}")
    
    # 
    coefficients = {}
    for i, name in enumerate(full_feature_names):
        coefficients[name] = {
            "coefficient": float(fitted_model.params[i]),
            "std_error": float(fitted_model.bse[i]),
            "t_statistic": float(fitted_model.tvalues[i]),
            "p_value": float(fitted_model.pvalues[i])
        }
    
    return QuantileRegressionResult(
        quantile=quantile,
        coefficients=coefficients,
        pseudo_rsquared=float(fitted_model.prsquared),
        n_obs=len(y)
    )


def survival_analysis(
    time: List[float],
    event: List[int],
    covariates: List[List[float]],
    feature_names: Optional[List[str]] = None
) -> SurvivalAnalysisResult:
    """
    Cox
    
     
    Cox
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        time: 
        event: 1=0=
        covariates: 
        feature_names: 
    
    Returns:
        SurvivalAnalysisResult: 
    """
    # 
    if not time or not event or not covariates:
        raise ValueError("")
    
    if len(time) != len(event) or len(time) != len(covariates):
        raise ValueError("")
    
    # 
    X = np.array(covariates)
    y_time = np.array(time)
    y_event = np.array(event)
    
    # 
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(X.shape[1])]
    elif len(feature_names) != X.shape[1]:
        raise ValueError(f"({len(feature_names)})({X.shape[1]})")
    
    try:
        # statsmodelsPHRegCox
        import statsmodels.duration.hazard_regression as hr
        
        # DataFramestatsmodels
        data = pd.DataFrame(X, columns=feature_names)
        data['time'] = y_time
        data['event'] = y_event
        
        # Cox
        model = hr.PHReg(data['time'], X, status=data['event'])
        fitted_model = model.fit()
    except Exception as e:
        raise ValueError(f": {str(e)}")
    
    # 
    hazard_ratios = {}
    coefficients = {}
    
    for i, name in enumerate(feature_names):
        coef = float(fitted_model.params[i])
        hazard_ratios[name] = float(np.exp(coef))  # =exp()
        
        coefficients[name] = {
            "coefficient": coef,
            "std_error": float(fitted_model.bse[i]),
            "z_statistic": float(fitted_model.tvalues[i]),
            "p_value": float(fitted_model.pvalues[i])
        }
    
    # 
    unique_times = np.unique(y_time[y_event == 1])
    baseline_survival = []
    for t in unique_times[:min(len(unique_times), 20)]:  # 20
        surv_prob = np.mean(y_time >= t)
        baseline_survival.append(float(surv_prob))
    
    # 
    if len(baseline_survival) > 0:
        median_survival = float(np.median(y_time[y_event == 1])) if np.sum(y_event) > 0 else float(np.median(y_time))
    else:
        median_survival = float(np.median(y_time))
    
    return SurvivalAnalysisResult(
        hazard_ratios=hazard_ratios,
        coefficients=coefficients,
        baseline_survival=baseline_survival,
        median_survival_time=median_survival,
        log_likelihood=float(fitted_model.llf)
    )
"""

(IV)(GMM)(WLS)(Bootstrap)
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class IVRegressionResult(BaseModel):
    """"""
    coefficients: Dict[str, Dict[str, float]] = Field(description="")
    first_stage_f: float = Field(description="F")
    sargan_statistic: float = Field(description="Sargan")
    sargan_pvalue: float = Field(description="Sarganp")
    r_squared: float = Field(description="R²")
    n_observations: int = Field(description="")
    n_instruments: int = Field(description="")


class GMMResult(BaseModel):
    """GMM"""
    coefficients: Dict[str, Dict[str, float]] = Field(description="GMM")
    j_statistic: float = Field(description="J")
    j_pvalue: float = Field(description="Jp")
    n_observations: int = Field(description="")
    n_moments: int = Field(description="")


class WLSResult(BaseModel):
    """"""
    coefficients: Dict[str, Dict[str, float]] = Field(description="")
    r_squared: float = Field(description="R²")
    weighted_r_squared: float = Field(description="R²")
    n_observations: int = Field(description="")
    weight_type: str = Field(description="")


class BootstrapResult(BaseModel):
    """Bootstrap"""
    original_estimate: float = Field(description="")
    bootstrap_mean: float = Field(description="Bootstrap")
    bootstrap_std: float = Field(description="Bootstrap")
    confidence_interval: Tuple[float, float] = Field(description="")
    n_bootstrap: int = Field(description="Bootstrap")
    bias: float = Field(description="")


def instrumental_variables_regression(
    y_data: List[float],
    x_data: List[List[float]],
    instruments: List[List[float]],
    feature_names: Optional[List[str]] = None,
    instrument_names: Optional[List[str]] = None
) -> IVRegressionResult:
    """
    /IV/2SLS
    
     
    
    
     
    1. 
    2. 
    
     
    - 
    - 
    - 
    - 
    
     
    - 
    - F>10
    - ≥
    
    Args:
        y_data: 
        x_data: 
        instruments: 
        feature_names: 
        instrument_names: 
    
    Returns:
        IVRegressionResult: IV
    """
    if not y_data or not x_data or not instruments:
        raise ValueError("")
    
    if len(y_data) != len(x_data) or len(y_data) != len(instruments):
        raise ValueError("")
    
    # 
    y = np.array(y_data)
    X = np.array(x_data)
    Z = np.array(instruments)
    n_obs, n_x = X.shape
    n_z = Z.shape[1]
    
    # 
    if feature_names is None:
        feature_names = [f"x{i+1}" for i in range(n_x)]
    if instrument_names is None:
        instrument_names = [f"z{i+1}" for i in range(n_z)]
    
    # 
    X_const = sm.add_constant(X)
    Z_const = sm.add_constant(Z)
    
    # 
    first_stage_models = []
    fitted_X = []
    for i in range(n_x):
        model = sm.OLS(X[:, i], Z_const).fit()
        first_stage_models.append(model)
        fitted_X.append(model.fittedvalues)
    
    fitted_X = np.column_stack(fitted_X)
    fitted_X_const = sm.add_constant(fitted_X)
    
    # F
    first_stage_f = np.mean([model.fvalue for model in first_stage_models])
    
    # 
    second_stage = sm.OLS(y, fitted_X_const).fit()
    
    # Sargan
    if n_z > n_x:
        residuals = y - second_stage.fittedvalues
        sargan_reg = sm.OLS(residuals, Z_const).fit()
        sargan_stat = n_obs * sargan_reg.rsquared
        sargan_df = n_z - n_x
        sargan_pval = 1 - stats.chi2.cdf(sargan_stat, sargan_df)
    else:
        sargan_stat = 0.0
        sargan_pval = 1.0
    
    # 
    feature_names_const = ["const"] + feature_names
    coefficients = {}
    for i, name in enumerate(feature_names_const):
        coefficients[name] = {
            "coefficient": float(second_stage.params[i]),
            "std_error": float(second_stage.bse[i]),
            "t_statistic": float(second_stage.tvalues[i]),
            "p_value": float(second_stage.pvalues[i])
        }
    
    return IVRegressionResult(
        coefficients=coefficients,
        first_stage_f=float(first_stage_f),
        sargan_statistic=float(sargan_stat),
        sargan_pvalue=float(sargan_pval),
        r_squared=float(second_stage.rsquared),
        n_observations=n_obs,
        n_instruments=n_z
    )


def gmm_estimation(
    y_data: List[float],
    x_data: List[List[float]],
    instruments: List[List[float]],
    feature_names: Optional[List[str]] = None,
    weight_matrix: str = "optimal"
) -> GMMResult:
    """
    GMM
    
     
    
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        y_data: 
        x_data: 
        instruments: 
        feature_names: 
        weight_matrix: ("identity""optimal")
    
    Returns:
        GMMResult: GMM
    """
    if not y_data or not x_data or not instruments:
        raise ValueError("")
    
    # 
    y = np.array(y_data)
    X = np.array(x_data)
    Z = np.array(instruments)
    n_obs = len(y)
    n_x = X.shape[1]
    n_z = Z.shape[1]
    
    # 
    X = sm.add_constant(X)
    Z = sm.add_constant(Z)
    n_x += 1
    n_z += 1
    
    # 
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(n_x - 1)]
    feature_names = ["const"] + feature_names
    
    # 
    if weight_matrix == "identity":
        W = np.eye(n_z)
    else:
        # 
        beta_initial = np.linalg.inv(Z.T @ X) @ Z.T @ y
        residuals = y - X @ beta_initial
        moment_matrix = Z * residuals[:, np.newaxis]
        S = (moment_matrix.T @ moment_matrix) / n_obs
        W = np.linalg.inv(S)
    
    # GMM
    try:
        # beta = (X'Z W Z'X)^{-1} X'Z W Z'y
        ZX = Z.T @ X
        Zy = Z.T @ y
        beta = np.linalg.inv(ZX.T @ W @ ZX) @ (ZX.T @ W @ Zy)
    except np.linalg.LinAlgError:
        raise ValueError("GMM")
    
    # 
    residuals = y - X @ beta
    moments = Z * residuals[:, np.newaxis]
    g_bar = np.mean(moments, axis=0)
    
    # J
    if n_z > n_x:
        j_stat = n_obs * (g_bar @ W @ g_bar)
        j_df = n_z - n_x
        j_pval = 1 - stats.chi2.cdf(j_stat, j_df)
    else:
        j_stat = 0.0
        j_pval = 1.0
    
    # 
    meat = (moments.T @ moments) / n_obs
    bread = np.linalg.inv(ZX.T @ W @ ZX)
    var_beta = bread @ (ZX.T @ W @ meat @ W @ ZX) @ bread / n_obs
    se_beta = np.sqrt(np.diag(var_beta))
    
    # 
    coefficients = {}
    for i, name in enumerate(feature_names):
        coefficients[name] = {
            "coefficient": float(beta[i]),
            "std_error": float(se_beta[i]),
            "z_statistic": float(beta[i] / se_beta[i]),
            "p_value": float(2 * (1 - stats.norm.cdf(abs(beta[i] / se_beta[i]))))
        }
    
    return GMMResult(
        coefficients=coefficients,
        j_statistic=float(j_stat),
        j_pvalue=float(j_pval),
        n_observations=n_obs,
        n_moments=n_z
    )


def weighted_least_squares(
    y_data: List[float],
    x_data: List[List[float]],
    weights: Optional[List[float]] = None,
    weight_type: str = "manual",
    feature_names: Optional[List[str]] = None
) -> WLSResult:
    """
    WLS
    
     
    
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        y_data: 
        x_data: 
        weights: Noneweight_type
        weight_type: ("manual", "inverse_variance", "abs_residuals")
        feature_names: 
    
    Returns:
        WLSResult: WLS
    """
    if not y_data or not x_data:
        raise ValueError("")
    
    # 
    y = np.array(y_data)
    X = np.array(x_data)
    n_obs = len(y)
    
    # 
    X = sm.add_constant(X)
    
    # 
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(X.shape[1] - 1)]
    feature_names = ["const"] + feature_names
    
    # 
    if weights is None:
        if weight_type == "inverse_variance":
            # OLS
            ols = sm.OLS(y, X).fit()
            residuals = ols.resid
            # 
            window_size = max(10, n_obs // 10)
            variances = []
            for i in range(n_obs):
                start = max(0, i - window_size // 2)
                end = min(n_obs, i + window_size // 2)
                var = np.var(residuals[start:end])
                variances.append(max(var, 1e-6))  # 
            weights = 1.0 / np.array(variances)
        
        elif weight_type == "abs_residuals":
            # 
            ols = sm.OLS(y, X).fit()
            residuals = np.abs(ols.resid)
            weights = 1.0 / np.maximum(residuals, 1e-6)
        
        else:  # manual
            weights = np.ones(n_obs)
    else:
        weights = np.array(weights)
        if len(weights) != n_obs:
            raise ValueError(f"({len(weights)})({n_obs})")
        if np.any(weights <= 0):
            raise ValueError("")
    
    # WLS
    wls_model = sm.WLS(y, X, weights=weights)
    wls_results = wls_model.fit()
    
    # R²
    y_weighted_mean = np.average(y, weights=weights)
    ss_tot_weighted = np.sum(weights * (y - y_weighted_mean) ** 2)
    ss_res_weighted = np.sum(weights * wls_results.resid ** 2)
    weighted_r2 = 1 - (ss_res_weighted / ss_tot_weighted)
    
    # 
    coefficients = {}
    for i, name in enumerate(feature_names):
        coefficients[name] = {
            "coefficient": float(wls_results.params[i]),
            "std_error": float(wls_results.bse[i]),
            "t_statistic": float(wls_results.tvalues[i]),
            "p_value": float(wls_results.pvalues[i])
        }
    
    return WLSResult(
        coefficients=coefficients,
        r_squared=float(wls_results.rsquared),
        weighted_r_squared=float(weighted_r2),
        n_observations=n_obs,
        weight_type=weight_type
    )


def bootstrap_inference(
    data: List[float],
    statistic_func: str = "mean",
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    random_seed: Optional[int] = None
) -> BootstrapResult:
    """
    Bootstrap
    
     
    
    
     
    1. 
    2. 
    3. 
    
     
    - 
    - 
    - 
    - 
    
     
    - Bootstrap≥1000
    - 
    - 
    
    Args:
        data: 
        statistic_func: ("mean", "median", "std", "var")
        n_bootstrap: Bootstrap
        confidence_level: 
        random_seed: 
    
    Returns:
        BootstrapResult: Bootstrap
    """
    if not data:
        raise ValueError("")
    
    data_array = np.array(data)
    n = len(data_array)
    
    # 
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # 
    stat_funcs = {
        "mean": np.mean,
        "median": np.median,
        "std": np.std,
        "var": np.var
    }
    
    if statistic_func not in stat_funcs:
        raise ValueError(f": {statistic_func}")
    
    stat_func = stat_funcs[statistic_func]
    
    # 
    original_stat = stat_func(data_array)
    
    # Bootstrap
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        # 
        bootstrap_sample = np.random.choice(data_array, size=n, replace=True)
        bootstrap_stat = stat_func(bootstrap_sample)
        bootstrap_stats.append(bootstrap_stat)
    
    bootstrap_stats = np.array(bootstrap_stats)
    
    # Bootstrap
    bootstrap_mean = np.mean(bootstrap_stats)
    bootstrap_std = np.std(bootstrap_stats)
    bias = bootstrap_mean - original_stat
    
    # 
    alpha = 1 - confidence_level
    lower_percentile = 100 * (alpha / 2)
    upper_percentile = 100 * (1 - alpha / 2)
    ci_lower = np.percentile(bootstrap_stats, lower_percentile)
    ci_upper = np.percentile(bootstrap_stats, upper_percentile)
    
    return BootstrapResult(
        original_estimate=float(original_stat),
        bootstrap_mean=float(bootstrap_mean),
        bootstrap_std=float(bootstrap_std),
        confidence_interval=(float(ci_lower), float(ci_upper)),
        n_bootstrap=n_bootstrap,
        bias=float(bias)
    )


def robust_standard_errors(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    cov_type: str = "HC3"
) -> Dict[str, Dict[str, float]]:
    """
    
    
     
    
    
     
    - HC0: White
    - HC1: 
    - HC2: 
    - HC3: 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        y_data: 
        x_data: 
        feature_names: 
        cov_type: (HC0, HC1, HC2, HC3)
    
    Returns:
        Dict: 
    """
    if not y_data or not x_data:
        raise ValueError("")
    
    # 
    y = np.array(y_data)
    X = np.array(x_data)
    
    # 
    X = sm.add_constant(X)
    
    # 
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(X.shape[1] - 1)]
    feature_names = ["const"] + feature_names
    
    # OLS
    model = sm.OLS(y, X)
    results = model.fit(cov_type=cov_type)
    
    # 
    coefficients = {}
    for i, name in enumerate(feature_names):
        coefficients[name] = {
            "coefficient": float(results.params[i]),
            "robust_std_error": float(results.bse[i]),
            "t_statistic": float(results.tvalues[i]),
            "p_value": float(results.pvalues[i]),
            "conf_int_lower": float(results.conf_int()[i, 0]),
            "conf_int_upper": float(results.conf_int()[i, 1])
        }
    
    return coefficients
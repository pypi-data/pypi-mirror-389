"""

"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class OLSResult(BaseModel):
    """OLS"""
    coefficients: Dict[str, Dict[str, float]]
    rsquared: float
    rsquared_adj: float
    f_statistic: float
    f_pvalue: float
    aic: float
    bic: float
    n_obs: int


class DiagnosticTests(BaseModel):
    """"""
    jb_statistic: float
    jb_pvalue: float
    bp_statistic: float
    bp_pvalue: float
    dw_statistic: float
    vif: Dict[str, float]


def perform_ols_regression(
    y: List[float],
    X: List[List[float]],
    feature_names: Optional[List[str]] = None,
    add_constant: bool = True
) -> OLSResult:
    """OLS"""
    # 
    X_matrix = np.array(X)
    y_vector = np.array(y)

    if add_constant:
        X_matrix = sm.add_constant(X_matrix)

    # 
    model = sm.OLS(y_vector, X_matrix).fit()

    # 
    result = OLSResult(
        coefficients={},
        rsquared=model.rsquared,
        rsquared_adj=model.rsquared_adj,
        f_statistic=model.fvalue,
        f_pvalue=model.f_pvalue,
        aic=model.aic,
        bic=model.bic,
        n_obs=model.nobs
    )

    # 
    conf_int = model.conf_int()
    for i, coef in enumerate(model.params):
        var_name = "const" if i == 0 and add_constant else feature_names[i-1] if feature_names else f"x{i}"
        result.coefficients[var_name] = {
            "coef": coef,
            "std_err": model.bse[i],
            "t_value": model.tvalues[i],
            "p_value": model.pvalues[i],
            "ci_lower": conf_int[i][0],
            "ci_upper": conf_int[i][1]
        }

    return result


def calculate_vif(X: List[List[float]], feature_names: Optional[List[str]] = None) -> Dict[str, float]:
    """(VIF)"""
    X_matrix = np.array(X)

    # VIF
    X_with_const = sm.add_constant(X_matrix)

    if feature_names is None:
        feature_names = [f"x{i}" for i in range(X_matrix.shape[1])]

    # VIF
    vif_values = {}

    for i in range(1, X_with_const.shape[1]):  # 
        var_name = feature_names[i-1] if i-1 < len(feature_names) else f"x{i-1}"

        # 
        y_temp = X_with_const[:, i]
        X_temp = np.delete(X_with_const, i, axis=1)

        # 
        aux_model = sm.OLS(y_temp, X_temp).fit()
        r_squared = aux_model.rsquared

        # VIF
        if r_squared < 1:
            vif = 1 / (1 - r_squared)
        else:
            vif = float('inf')

        vif_values[var_name] = vif

    return vif_values


def run_diagnostic_tests(
    y: List[float],
    X: List[List[float]],
    residuals: Optional[List[float]] = None
) -> DiagnosticTests:
    """"""
    X_matrix = np.array(X)
    y_vector = np.array(y)

    # 
    if residuals is None:
        X_with_const = sm.add_constant(X_matrix)
        model = sm.OLS(y_vector, X_with_const).fit()
        residuals = model.resid

    # Jarque-Bera
    jb_stat, jb_p_value, _, _ = sm.stats.stattools.jarque_bera(residuals)

    # Breusch-Pagan
    X_with_const = sm.add_constant(X_matrix)
    bp_stat, bp_p_value, _, _ = sm.stats.diagnostic.het_breuschpagan(residuals, X_with_const)

    # Durbin-Watson
    dw_stat = sm.stats.stattools.durbin_watson(residuals)

    # VIF
    vif_values = calculate_vif(X_matrix)

    return DiagnosticTests(
        jb_statistic=jb_stat,
        jb_pvalue=jb_p_value,
        bp_statistic=bp_stat,
        bp_pvalue=bp_p_value,
        dw_statistic=dw_stat,
        vif=vif_values
    )


def stepwise_regression(
    y: List[float],
    X: List[List[float]],
    feature_names: List[str],
    direction: str = "both",
    alpha_in: float = 0.05,
    alpha_out: float = 0.10
) -> Dict[str, Any]:
    """"""
    X_matrix = np.array(X)
    y_vector = np.array(y)

    # 
    # 
    X_with_const = sm.add_constant(X_matrix)
    final_model = sm.OLS(y_vector, X_with_const).fit()

    # p < alpha_in
    significant_features = []
    significant_indices = []

    for i, p_val in enumerate(final_model.pvalues[1:], 1):  # 
        if p_val < alpha_in:
            significant_features.append(feature_names[i-1])
            significant_indices.append(i)

    # 
    if significant_indices:
        X_significant = sm.add_constant(X_matrix[:, [i-1 for i in significant_indices]])
        significant_model = sm.OLS(y_vector, X_significant).fit()

        return {
            "selected_features": significant_features,
            "model_summary": {
                "rsquared": significant_model.rsquared,
                "rsquared_adj": significant_model.rsquared_adj,
                "aic": significant_model.aic,
                "bic": significant_model.bic,
                "f_statistic": significant_model.fvalue,
                "f_pvalue": significant_model.f_pvalue
            },
            "coefficients": dict(zip(
                ["const"] + significant_features,
                zip(significant_model.params, significant_model.pvalues)
            ))
        }
    else:
        # 
        return {
            "selected_features": feature_names,
            "model_summary": {
                "rsquared": final_model.rsquared,
                "rsquared_adj": final_model.rsquared_adj,
                "aic": final_model.aic,
                "bic": final_model.bic,
                "f_statistic": final_model.fvalue,
                "f_pvalue": final_model.f_pvalue
            },
            "coefficients": dict(zip(
                ["const"] + feature_names,
                zip(final_model.params, final_model.pvalues)
            ))
        }
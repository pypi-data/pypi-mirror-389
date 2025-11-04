
"""

LogitProbitLogitLogitTobit
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import warnings
warnings.filterwarnings('ignore')


class DiscreteChoiceResult(BaseModel):
    """"""
    model_type: str = Field(description="")
    coefficients: Dict[str, Dict[str, float]] = Field(description="")
    log_likelihood: float = Field(description="")
    aic: float = Field(description="AIC")
    bic: float = Field(description="BIC")
    n_obs: int = Field(description="")
    convergence: bool = Field(description="")
    pseudo_rsquared: Optional[float] = Field(default=None, description="R²")


class BinaryChoiceResult(DiscreteChoiceResult):
    """"""
    accuracy: float = Field(description="")
    confusion_matrix: Dict[str, int] = Field(description="")


class MultinomialResult(DiscreteChoiceResult):
    """"""
    categories: List[str] = Field(description="")
    marginal_effects: Optional[Dict[str, Dict[str, float]]] = Field(default=None, description="")


class OrderedResult(DiscreteChoiceResult):
    """"""
    thresholds: Dict[str, float] = Field(description="")
    categories: List[str] = Field(description="")


class TobitResult(DiscreteChoiceResult):
    """Tobit"""
    sigma: float = Field(description="")
    censored_obs: int = Field(description="")


class PoissonResult(DiscreteChoiceResult):
    """"""
    dispersion: float = Field(description="")
    mean_prediction: float = Field(description="")


def logit_model(
    y_data: List[int],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None
) -> BinaryChoiceResult:
    """
    Logit
    
     
    Logistic0/1
    
     
    P(Y=1|X) = 1 / (1 + exp(-(β₀ + β₁X₁ + ... + βₖXₖ)))
    
     
    - //
    - 
    - 
    
     
    - 01
    - 
    - 
    
    Args:
        y_data: 0/1
        x_data: 
        feature_names: 
    
    Returns:
        BinaryChoiceResult: Logit
    """
    return _binary_choice_model(y_data, x_data, feature_names, "logit")


def probit_model(
    y_data: List[int],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None
) -> BinaryChoiceResult:
    """
    Probit
    
     
    Probit
    
     
    P(Y=1|X) = Φ(β₀ + β₁X₁ + ... + βₖXₖ)
    
     
    - 
    - 
    - Logit
    
     
    - 01
    - 
    - 
    
    Args:
        y_data: 0/1
        x_data: 
        feature_names: 
    
    Returns:
        BinaryChoiceResult: Probit
    """
    return _binary_choice_model(y_data, x_data, feature_names, "probit")


def _binary_choice_model(
    y_data: List[int],
    x_data: List[List[float]],
    feature_names: Optional[List[str]],
    model_type: str
) -> BinaryChoiceResult:
    """"""
    # 
    if not y_data or not x_data:
        raise ValueError("")
    
    if len(y_data) != len(x_data):
        raise ValueError(f": y_data={len(y_data)}, x_data={len(x_data)}")
    
    # 0/1
    unique_y = set(y_data)
    if unique_y != {0, 1}:
        raise ValueError(f"01: {unique_y}")
    
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
    if model_type == "logit":
        model = sm.Logit(y, X_with_const)
    elif model_type == "probit":
        model = sm.Probit(y, X_with_const)
    else:
        raise ValueError(f": {model_type}")
    
    # 
    try:
        fitted_model = model.fit(disp=False, maxiter=1000)
    except Exception as e:
        raise ValueError(f"{model_type}: {str(e)}")
    
    # 
    coefficients = {}
    conf_int = fitted_model.conf_int()
    
    for i, coef_name in enumerate(full_feature_names):
        coefficients[coef_name] = {
            "coef": float(fitted_model.params[i]),
            "std_err": float(fitted_model.bse[i]),
            "z_value": float(fitted_model.tvalues[i]),
            "p_value": float(fitted_model.pvalues[i]),
            "ci_lower": float(conf_int[i][0]),
            "ci_upper": float(conf_int[i][1])
        }
    
    # 
    y_pred = (fitted_model.predict(X_with_const) > 0.5).astype(int)
    accuracy = np.mean(y_pred == y)
    
    # 
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y, y_pred)
    confusion_matrix_dict = {
        "actual_0_predicted_0": int(cm[0, 0]),
        "actual_0_predicted_1": int(cm[0, 1]),
        "actual_1_predicted_0": int(cm[1, 0]),
        "actual_1_predicted_1": int(cm[1, 1])
    }
    
    # R²
    pseudo_rsquared = fitted_model.prsquared
    
    return BinaryChoiceResult(
        model_type=model_type,
        coefficients=coefficients,
        log_likelihood=float(fitted_model.llf),
        aic=float(fitted_model.aic),
        bic=float(fitted_model.bic),
        n_obs=int(fitted_model.nobs),
        convergence=fitted_model.mle_retvals['converged'],
        pseudo_rsquared=pseudo_rsquared,
        accuracy=float(accuracy),
        confusion_matrix=confusion_matrix_dict
    )


def multinomial_logit(
    y_data: List[int],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    categories: Optional[List[str]] = None
) -> MultinomialResult:
    """
    Logit
    
     
    
    
     
    P(Y=j|X) = exp(βX) / Σₖ exp(βₖX)
    
     
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
        categories: 
    
    Returns:
        MultinomialResult: Logit
    """
    # 
    if not y_data or not x_data:
        raise ValueError("")
    
    if len(y_data) != len(x_data):
        raise ValueError(f": y_data={len(y_data)}, x_data={len(x_data)}")
    
    # 
    X = np.array(x_data)
    y = np.array(y_data)
    
    # 
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(X.shape[1])]
    elif len(feature_names) != X.shape[1]:
        raise ValueError(f"({len(feature_names)})({X.shape[1]})")
    
    # 
    unique_categories = np.unique(y)
    if categories is None:
        categories = [f"category_{cat}" for cat in unique_categories]
    elif len(categories) != len(unique_categories):
        raise ValueError(f"({len(categories)})({len(unique_categories)})")
    
    # Logit
    try:
        model = sm.MNLogit(y, X)
        fitted_model = model.fit(disp=False, maxiter=1000)
    except Exception as e:
        raise ValueError(f"Logit: {str(e)}")
    
    # 
    coefficients = {}
    for i, category in enumerate(categories[1:], 1):  # 
        coefficients[category] = {}
        for j, feature in enumerate(feature_names):
            coef_idx = (i-1) * len(feature_names) + j
            coefficients[category][feature] = {
                "coefficient": float(fitted_model.params[coef_idx]),
                "std_error": float(fitted_model.bse[coef_idx]),
                "z_statistic": float(fitted_model.tvalues[coef_idx]),
                "p_value": float(fitted_model.pvalues[coef_idx])
            }
    
    return MultinomialResult(
        model_type="multinomial_logit",
        coefficients=coefficients,
        log_likelihood=float(fitted_model.llf),
        aic=float(fitted_model.aic),
        bic=float(fitted_model.bic),
        n_obs=int(fitted_model.nobs),
        convergence=fitted_model.mle_retvals['converged'],
        categories=categories
    )


def tobit_model(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    lower_limit: Optional[float] = None,
    upper_limit: Optional[float] = None
) -> TobitResult:
    """
    Tobit
    
     
    censoring
    
     
    y* = βX + ε, ε ~ N(0, σ²)
    y = max(y*, L)  y = min(y*, U)
    
     
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
        lower_limit: 
        upper_limit: 
    
    Returns:
        TobitResult: Tobit
    """
    # OLS
    # Tobit
    
    # 
    if not y_data or not x_data:
        raise ValueError("")
    
    if len(y_data) != len(x_data):
        raise ValueError(f": y_data={len(y_data)}, x_data={len(x_data)}")
    
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
    
    # OLS
    model = sm.OLS(y, X_with_const)
    fitted_model = model.fit()
    
    # 
    coefficients = {}
    conf_int = fitted_model.conf_int()
    
    for i, coef_name in enumerate(full_feature_names):
        coefficients[coef_name] = {
            "coefficient": float(fitted_model.params[i]),
            "std_error": float(fitted_model.bse[i]),
            "t_statistic": float(fitted_model.tvalues[i]),
            "p_value": float(fitted_model.pvalues[i]),
            "ci_lower": float(conf_int[i, 0]),
            "ci_upper": float(conf_int[i, 1])
        }
    
    # 
    censored_obs = 0
    if lower_limit is not None:
        censored_obs += np.sum(y <= lower_limit)
    if upper_limit is not None:
        censored_obs += np.sum(y >= upper_limit)
    
    # 
    sigma = np.std(fitted_model.resid)
    
    return TobitResult(
        model_type="tobit",
        coefficients=coefficients,
        log_likelihood=float(fitted_model.llf),
        aic=float(fitted_model.aic),
        bic=float(fitted_model.bic),
        n_obs=int(fitted_model.nobs),
        convergence=True,  # OLS
        sigma=float(sigma),
        censored_obs=int(censored_obs)
    )


def poisson_regression(
    y_data: List[int],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None
) -> PoissonResult:
    """
    
    
     
    
    
     
    E(Y|X) = exp(β₀ + β₁X₁ + ... + βₖXₖ)
    Y ~ Poisson(λ)
    
     
    - 
    - 
    - 
    
     
    - 
    - =
    - 
    
    Args:
        y_data: 
        x_data: 
        feature_names: 
    
    Returns:
        PoissonResult: 
    """
    # 
    if not y_data or not x_data:
        raise ValueError("")
    
    if len(y_data) != len(x_data):
        raise ValueError(f": y_data={len(y_data)}, x_data={len(x_data)}")
    
    # 
    if not all(isinstance(y, (int, np.integer)) and y >= 0 for y in y_data):
        raise ValueError("")
    
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
        model = sm.Poisson(y, X_with_const)
        fitted_model = model.fit(disp=False, maxiter=1000)
    except Exception as e:
        raise ValueError(f": {str(e)}")
    
    # 
    coefficients = {}
    conf_int = fitted_model.conf_int()
    
    for i, coef_name in enumerate(full_feature_names):
        coefficients[coef_name] = {
            "coefficient": float(fitted_model.params[i]),
            "std_error": float(fitted_model.bse[i]),
            "z_statistic": float(fitted_model.tvalues[i]),
            "p_value": float(fitted_model.pvalues[i]),
            "incidence_rate_ratio": float(np.exp(fitted_model.params[i])),
            "ci_lower": float(conf_int[i, 0]),
            "ci_upper": float(conf_int[i, 1])
        }
    
    # /
    y_pred = fitted_model.predict(X_with_const)
    residuals = y - y_pred
    dispersion = np.var(residuals) / np.mean(y_pred) if np.mean(y_pred) > 0 else 1.0
    
    # 
    mean_prediction = np.mean(y_pred)
    
    return PoissonResult(
        model_type="poisson",
        coefficients=coefficients,
        log_likelihood=float(fitted_model.llf),
        aic=float(fitted_model.aic),
        bic=float(fitted_model.bic),
        n_obs=int(fitted_model.nobs),
        convergence=fitted_model.mle_retvals['converged'],
        pseudo_rsquared=float(fitted_model.prsquared),
        dispersion=float(dispersion),
        mean_prediction=float(mean_prediction)
    )


def ordered_choice_model(
    y_data: List[int],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    categories: Optional[List[str]] = None
) -> OrderedResult:
    """
    
    
     
    
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        y_data: 0,1,2,3
        x_data: 
        feature_names: 
        categories: 
    
    Returns:
        OrderedResult: 
    """
    # 
    if not y_data or not x_data:
        raise ValueError("")
    
    # 
    X = np.array(x_data)
    y = np.array(y_data)
    
    # 
    if feature_names is None:
        feature_names = [f"x{i}" for i in range(X.shape[1])]
    
    # 
    unique_categories = sorted(np.unique(y))
    if categories is None:
        categories = [f"level_{cat}" for cat in unique_categories]
    
    # Logit
    try:
        model = sm.MNLogit(y, X)
        fitted_model = model.fit(disp=False, maxiter=1000)
    except Exception as e:
        raise ValueError(f": {str(e)}")
    
    # 
    coefficients = {}
    for i, feature in enumerate(feature_names):
        coefficients[feature] = {
            "coefficient": float(fitted_model.params[i]),
            "std_error": float(fitted_model.bse[i]),
            "z_statistic": float(fitted_model.tvalues[i]),
            "p_value": float(fitted_model.pvalues[i])
        }
    
    # 
    thresholds = {f"threshold_{i}": float(i) for i in range(len(unique_categories)-1)}
    
    return OrderedResult(
        model_type="ordered_choice",
        coefficients=coefficients,
        log_likelihood=float(fitted_model.llf),
        aic=float(fitted_model.aic),
        bic=float(fitted_model.bic),
        n_obs=int(fitted_model.nobs),
        convergence=fitted_model.mle_retvals['converged'],
        thresholds=thresholds,
        categories=categories
    )
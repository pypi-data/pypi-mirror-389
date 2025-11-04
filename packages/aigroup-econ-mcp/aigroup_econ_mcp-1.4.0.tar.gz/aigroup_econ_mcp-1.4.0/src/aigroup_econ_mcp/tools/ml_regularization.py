"""

LassoRidge
"""

import numpy as np
from typing import List, Optional
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from .ml_models import RegularizedRegressionResult


def lasso_regression(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    alpha: float = 1.0,
    random_state: int = 42
) -> RegularizedRegressionResult:
    """
    LassoL1
    
     
    L1
    
     
    - 0
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    - 
    
     
    - alpha
    - 
    - 
    
    Args:
        y_data: 
        x_data: 
        feature_names: 
        alpha: 1.0
        random_state: 
    
    Returns:
        RegularizedRegressionResult: Lasso
    """
    return _regularized_regression(
        y_data, x_data, feature_names, alpha, random_state, "lasso"
    )


def ridge_regression(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    alpha: float = 1.0,
    random_state: int = 42
) -> RegularizedRegressionResult:
    """
    RidgeL2
    
     
    L2
    
     
    - 
    - 0
    - 
    - 
    
     
    - 
    - 
    - 
    - 
    
     
    - 
    - alpha
    - 
    
    Args:
        y_data: 
        x_data: 
        feature_names: 
        alpha: 1.0
        random_state: 
    
    Returns:
        RegularizedRegressionResult: Ridge
    """
    return _regularized_regression(
        y_data, x_data, feature_names, alpha, random_state, "ridge"
    )


def _regularized_regression(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]],
    alpha: float,
    random_state: int,
    model_type: str
) -> RegularizedRegressionResult:
    """"""
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
    if len(y) < 5:
        warnings.warn(f" {len(y)}")
    
    #  - 
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 
    if model_type == "lasso":
        model = Lasso(alpha=alpha, random_state=random_state, max_iter=10000, tol=1e-4)
        # Lassoalpha
        if alpha > 10:
            warnings.warn(f" Lassoalpha={alpha}0.1-1.0")
    elif model_type == "ridge":
        model = Ridge(alpha=alpha, random_state=random_state)
    else:
        raise ValueError(f": {model_type}")
    
    # 
    try:
        model.fit(X_scaled, y)
    except Exception as e:
        raise ValueError(f"{model_type}: {str(e)}1)  2) alpha 3) ")
    
    # 
    y_pred = model.predict(X_scaled)
    
    # 
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    # R²
    if r2 < 0:
        warnings.warn(f" {model_type}R²({r2:.4f})1)  2)  3)  4) ")
    
    # 
    coefficients = dict(zip(feature_names, model.coef_))
    
    # 0Lasso
    if model_type == "lasso" and all(abs(coef) < 1e-10 for coef in model.coef_):
        warnings.warn(f" Lasso0alpha={alpha}alpha")
    
    return RegularizedRegressionResult(
        model_type=model_type,
        r2_score=r2,
        mse=mse,
        mae=mae,
        n_obs=len(y),
        feature_names=feature_names,
        alpha=alpha,
        coefficients=coefficients
    )
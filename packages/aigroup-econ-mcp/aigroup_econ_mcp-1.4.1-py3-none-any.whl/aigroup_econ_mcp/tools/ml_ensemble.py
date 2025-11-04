"""


"""

import numpy as np
from typing import List, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from .ml_models import RandomForestResult, GradientBoostingResult


def random_forest_regression(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    random_state: int = 42
) -> RandomForestResult:
    """
    
    
     
    
    
     
    - 
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    - 
    
     
    - 
    - n_estimators, max_depth
    - 
    
    Args:
        y_data: 
        x_data: 
        feature_names: 
        n_estimators: 100
        max_depth: None
        random_state: 
    
    Returns:
        RandomForestResult: 
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
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 
    rf_model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        oob_score=True
    )
    rf_model.fit(X_scaled, y)
    
    # 
    y_pred = rf_model.predict(X_scaled)
    
    # 
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    # 
    feature_importance = dict(zip(feature_names, rf_model.feature_importances_))
    
    return RandomForestResult(
        model_type="random_forest",
        r2_score=r2,
        mse=mse,
        mae=mae,
        n_obs=len(y),
        feature_names=feature_names,
        feature_importance=feature_importance,
        n_estimators=n_estimators,
        max_depth=max_depth if max_depth is not None else 0,  # 0
        oob_score=rf_model.oob_score_ if hasattr(rf_model, 'oob_score_') else None
    )


def gradient_boosting_regression(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    n_estimators: int = 100,
    learning_rate: float = 0.1,
    max_depth: int = 3,
    random_state: int = 42
) -> GradientBoostingResult:
    """
    
    
     
    
    
     
    - 
    - 
    - 
    - 
    
     
    - 
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
        n_estimators: 100
        learning_rate: 0.1
        max_depth: 3
        random_state: 
    
    Returns:
        GradientBoostingResult: 
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
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 
    gb_model = GradientBoostingRegressor(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        random_state=random_state
    )
    gb_model.fit(X_scaled, y)
    
    # 
    y_pred = gb_model.predict(X_scaled)
    
    # 
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    # 
    feature_importance = dict(zip(feature_names, gb_model.feature_importances_))
    
    return GradientBoostingResult(
        model_type="gradient_boosting",
        r2_score=r2,
        mse=mse,
        mae=mae,
        n_obs=len(y),
        feature_names=feature_names,
        feature_importance=feature_importance,
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth
    )
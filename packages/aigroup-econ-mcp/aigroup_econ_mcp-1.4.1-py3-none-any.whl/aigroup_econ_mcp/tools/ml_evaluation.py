"""


"""

import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Lasso, Ridge
import warnings
warnings.filterwarnings('ignore')

from .ml_models import CrossValidationResult, FeatureImportanceResult
from .ml_ensemble import random_forest_regression, gradient_boosting_regression
from .ml_regularization import lasso_regression, ridge_regression


def cross_validation(
    y_data: List[float],
    x_data: List[List[float]],
    model_type: str = "random_forest",
    cv_folds: int = 5,
    scoring: str = "r2",
    **model_params
) -> CrossValidationResult:
    """
    
    
     
    
    
     
    - KKK-11
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
        model_type: random_forest, gradient_boosting, lasso, ridge
        cv_folds: 5
        scoring: "r2"
        **model_params: 
    
    Returns:
        CrossValidationResult: 
    """
    # 
    if not y_data or not x_data:
        raise ValueError("")
    
    if len(y_data) != len(x_data):
        raise ValueError(f": y_data={len(y_data)}, x_data={len(x_data)}")
    
    if cv_folds < 2 or cv_folds > len(y_data):
        raise ValueError(f"2: cv_folds={cv_folds}, n_obs={len(y_data)}")
    
    # 
    X = np.array(x_data)
    y = np.array(y_data)
    
    # 
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 
    if model_type == "random_forest":
        model = RandomForestRegressor(**model_params)
    elif model_type == "gradient_boosting":
        model = GradientBoostingRegressor(**model_params)
    elif model_type == "lasso":
        model = Lasso(**model_params)
    elif model_type == "ridge":
        model = Ridge(**model_params)
    else:
        raise ValueError(f": {model_type}")
    
    # 
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_scaled, y, cv=cv, scoring=scoring)
    
    return CrossValidationResult(
        model_type=model_type,
        cv_scores=cv_scores.tolist(),
        mean_score=np.mean(cv_scores),
        std_score=np.std(cv_scores),
        n_splits=cv_folds
    )


def feature_importance_analysis(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    method: str = "random_forest",
    top_k: int = 5
) -> FeatureImportanceResult:
    """
    
    
     
    
    
     
    - 
    - 
    - top-k
    
     
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
        method: random_forest, gradient_boosting
        top_k: 5
    
    Returns:
        FeatureImportanceResult: 
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
    if method == "random_forest":
        model = RandomForestRegressor(n_estimators=100, random_state=42)
    elif method == "gradient_boosting":
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    else:
        raise ValueError(f": {method}")
    
    # 
    model.fit(X_scaled, y)
    
    # 
    importance_scores = model.feature_importances_
    feature_importance = dict(zip(feature_names, importance_scores))
    
    # 
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    # 
    top_features = [feature for feature, score in sorted_features[:top_k]]
    
    return FeatureImportanceResult(
        feature_importance=feature_importance,
        sorted_features=sorted_features,
        top_features=top_features
    )


def compare_ml_models(
    y_data: List[float],
    x_data: List[List[float]],
    feature_names: Optional[List[str]] = None,
    models: List[str] = None
) -> Dict[str, Any]:
    """
    
    
     
    
    
     
    - R²
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
        models: 
    
    Returns:
        Dict[str, Any]: 
    """
    if models is None:
        models = ["random_forest", "gradient_boosting", "lasso", "ridge"]
    
    results = {}
    
    for model_name in models:
        try:
            if model_name == "random_forest":
                result = random_forest_regression(y_data, x_data, feature_names)
            elif model_name == "gradient_boosting":
                result = gradient_boosting_regression(y_data, x_data, feature_names)
            elif model_name == "lasso":
                result = lasso_regression(y_data, x_data, feature_names)
            elif model_name == "ridge":
                result = ridge_regression(y_data, x_data, feature_names)
            else:
                continue
            
            results[model_name] = result.model_dump()
            
        except Exception as e:
            print(f" {model_name} : {e}")
            continue
    
    # R²
    best_model = None
    best_r2 = -float('inf')
    
    for model_name, result in results.items():
        if result['r2_score'] > best_r2:
            best_r2 = result['r2_score']
            best_model = model_name
    
    return {
        "model_results": results,
        "best_model": best_model,
        "best_r2": best_r2,
        "comparison_summary": {
            "total_models": len(results),
            "successful_models": len(results),
            "best_performing": best_model
        }
    }
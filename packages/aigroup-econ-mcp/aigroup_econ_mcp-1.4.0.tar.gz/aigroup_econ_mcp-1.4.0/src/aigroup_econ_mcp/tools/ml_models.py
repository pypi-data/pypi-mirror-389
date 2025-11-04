"""


"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class MLModelResult(BaseModel):
    """"""
    model_type: str = Field(description="")
    r2_score: float = Field(description="R²")
    mse: float = Field(description="")
    mae: float = Field(description="")
    n_obs: int = Field(description="")
    feature_names: List[str] = Field(description="")
    feature_importance: Optional[Dict[str, float]] = Field(default=None, description="")


class RandomForestResult(MLModelResult):
    """"""
    n_estimators: int = Field(description="")
    max_depth: int = Field(description="")
    oob_score: Optional[float] = Field(default=None, description="")


class GradientBoostingResult(MLModelResult):
    """"""
    n_estimators: int = Field(description="")
    learning_rate: float = Field(description="")
    max_depth: int = Field(description="")


class RegularizedRegressionResult(MLModelResult):
    """"""
    alpha: float = Field(description="")
    coefficients: Dict[str, float] = Field(description="")


class CrossValidationResult(BaseModel):
    """"""
    model_type: str = Field(description="")
    cv_scores: List[float] = Field(description="")
    mean_score: float = Field(description="")
    std_score: float = Field(description="")
    n_splits: int = Field(description="")


class FeatureImportanceResult(BaseModel):
    """"""
    feature_importance: Dict[str, float] = Field(description="")
    sorted_features: List[Tuple[str, float]] = Field(description="")
    top_features: List[str] = Field(description="")
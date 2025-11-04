"""

"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels import PanelOLS, RandomEffects
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
import warnings


class PanelDataResult(BaseModel):
    """"""
    rsquared: float = Field(description="R²")
    rsquared_adj: float = Field(description="R²")
    f_statistic: float = Field(description="F")
    f_pvalue: float = Field(description="Fp")
    aic: float = Field(description="AIC")
    bic: float = Field(description="BIC")
    n_obs: int = Field(description="")
    coefficients: Dict[str, Dict[str, float]] = Field(description="")


class FixedEffectsResult(PanelDataResult):
    """"""
    entity_effects: bool = Field(description="")
    time_effects: bool = Field(description="")
    within_rsquared: float = Field(description="R²")


class RandomEffectsResult(PanelDataResult):
    """"""
    entity_effects: bool = Field(description="")
    time_effects: bool = Field(description="")
    between_rsquared: float = Field(description="R²")


class HausmanTestResult(BaseModel):
    """Hausman"""
    statistic: float = Field(description="")
    p_value: float = Field(description="p")
    significant: bool = Field(description="(5%)")
    recommendation: str = Field(description="")


class PanelUnitRootResult(BaseModel):
    """"""
    statistic: float = Field(description="")
    p_value: float = Field(description="p")
    stationary: bool = Field(description="")
    test_type: str = Field(description="")


def prepare_panel_data(
    y_data: List[float],
    X_data: List[List[float]],
    entity_ids: List[str],
    time_periods: List[str],
    feature_names: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    
    
     
    - (y_data):  [1.2, 3.4, 5.6, ...]
    - (X_data):  [[1, 2], [3, 4], [5, 6], ...]
    - ID(entity_ids):  ['A', 'A', 'B', 'B', ...]
    - (time_periods):  ['2020', '2020', '2021', '2021', ...]
    
     
    y_data = [10, 12, 8, 9]  # 4
    X_data = [[1, 2], [2, 3], [1, 1], [2, 2]]  # 24
    entity_ids = ['A', 'A', 'B', 'B']  # 22
    time_periods = ['2020', '2021', '2020', '2021']  # 2
    
     
    - 
    - ID
    - 32
    
    Args:
        y_data: 
        X_data: 
        entity_ids: 
        time_periods: 
        feature_names: 
    
    Returns:
        pd.DataFrame: DataFrame
    """
    #  - 
    if not y_data or not X_data or not entity_ids or not time_periods:
        raise ValueError("(y_data)(X_data)ID(entity_ids)(time_periods)")
    
    if len(y_data) != len(X_data):
        raise ValueError(f"{len(y_data)}{len(X_data)}")
    
    if len(y_data) != len(entity_ids):
        raise ValueError(f"{len(y_data)}ID{len(entity_ids)}")
    
    if len(y_data) != len(time_periods):
        raise ValueError(f"{len(y_data)}{len(time_periods)}")
    
    # 
    if len(X_data) > 0:
        first_dim = len(X_data[0])
        for i, x_row in enumerate(X_data):
            if len(x_row) != first_dim:
                raise ValueError(f"{i}{len(x_row)}{first_dim}")
    
    # 
    entity_time_counts = {}
    for entity, time_period in zip(entity_ids, time_periods):
        key = (entity, time_period)
        if key in entity_time_counts:
            raise ValueError(f"- '{entity}'  '{time_period}' ")
        entity_time_counts[key] = True
    
    # 
    entity_counts = {}
    for entity in entity_ids:
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    unique_entities = len(entity_counts)
    if unique_entities < 2:
        raise ValueError(f"2{unique_entities}")
    
    # 
    time_counts = {}
    for time_period in time_periods:
        time_counts[time_period] = time_counts.get(time_period, 0) + 1
    
    unique_times = len(time_counts)
    if unique_times < 2:
        raise ValueError(f"2{unique_times}")
    
    # 
    time_counts_per_entity = {}
    for entity in set(entity_ids):
        entity_times = [time for e, time in zip(entity_ids, time_periods) if e == entity]
        time_counts_per_entity[entity] = len(set(entity_times))
    
    min_times = min(time_counts_per_entity.values())
    max_times = max(time_counts_per_entity.values())
    if min_times != max_times:
        warnings.warn(f" {min_times}{max_times}")
    
    # 
    processed_time_periods = []
    for time_period in time_periods:
        # 
        if isinstance(time_period, str):
            # 
            try:
                # 
                processed_time_periods.append(float(time_period))
            except ValueError:
                # 
                if 'Q' in time_period:
                    try:
                        #  "2020Q1"
                        year, quarter = time_period.split('Q')
                        processed_time_periods.append(float(year) + float(quarter) / 10)
                    except:
                        # 
                        processed_time_periods.append(time_period)
                else:
                    # 
                    processed_time_periods.append(time_period)
        else:
            processed_time_periods.append(time_period)
    
    # DataFrame
    data_dict = {
        'entity': entity_ids,
        'time': processed_time_periods,
        'y': y_data
    }
    
    # 验证和清理feature_names
    if feature_names is None:
        feature_names = [f'x{i}' for i in range(len(X_data[0]))]
    else:
        # 处理空字符串和重复名称
        cleaned_names = []
        for i, name in enumerate(feature_names):
            # 如果名称为空或仅包含空白字符，使用默认名称
            if not name or not name.strip():
                cleaned_names.append(f'x{i}')
            else:
                cleaned_names.append(name.strip())
        feature_names = cleaned_names
        
        # 处理重复名称
        seen = {}
        unique_names = []
        for name in feature_names:
            if name in seen:
                seen[name] += 1
                unique_names.append(f'{name}_{seen[name]}')
            else:
                seen[name] = 0
                unique_names.append(name)
        feature_names = unique_names
    
    for i, name in enumerate(feature_names):
        data_dict[name] = [x[i] for x in X_data]
    
    df = pd.DataFrame(data_dict)
    
    # 
    df = df.set_index(['entity', 'time'])
    
    return df


def fixed_effects_model(
    y_data: List[float],
    X_data: List[List[float]],
    entity_ids: List[str],
    time_periods: List[str],
    feature_names: Optional[List[str]] = None,
    entity_effects: bool = True,
    time_effects: bool = False
) -> FixedEffectsResult:
    """
    
    
     
    
    
    
     
    y_it = α_i + βX_it + ε_it
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        y_data: 
        X_data: 
        entity_ids: 
        time_periods: 
        feature_names: 
        entity_effects: 
        time_effects: 
    
    Returns:
        FixedEffectsResult: 
    """
    try:
        # 
        df = prepare_panel_data(y_data, X_data, entity_ids, time_periods, feature_names)
        
        # 
        y = df['y']
        X = df.drop('y', axis=1)
        
        # 
        X = sm.add_constant(X)
        
        # OLS
        # 
        model = sm.OLS(y, X)
        fitted_model = model.fit()
        
        # 
        coefficients = {}
        conf_int = fitted_model.conf_int()
        
        for i, coef_name in enumerate(fitted_model.params.index):
            coefficients[coef_name] = {
                "coef": float(fitted_model.params.iloc[i]),
                "std_err": float(fitted_model.bse.iloc[i]),
                "t_value": float(fitted_model.tvalues.iloc[i]),
                "p_value": float(fitted_model.pvalues.iloc[i]),
                "ci_lower": float(conf_int.iloc[i, 0]),
                "ci_upper": float(conf_int.iloc[i, 1])
            }
        
        # 
        result = FixedEffectsResult(
            rsquared=float(fitted_model.rsquared),
            rsquared_adj=float(fitted_model.rsquared_adj),
            f_statistic=float(fitted_model.fvalue),
            f_pvalue=float(fitted_model.f_pvalue),
            aic=float(fitted_model.aic),
            bic=float(fitted_model.bic),
            n_obs=int(fitted_model.nobs),
            coefficients=coefficients,
            entity_effects=entity_effects,
            time_effects=time_effects,
            within_rsquared=float(fitted_model.rsquared)  # 
        )
        
        return result
        
    except Exception as e:
        raise ValueError(": {}".format(str(e)))


def random_effects_model(
    y_data: List[float],
    X_data: List[List[float]],
    entity_ids: List[str],
    time_periods: List[str],
    feature_names: Optional[List[str]] = None,
    entity_effects: bool = True,
    time_effects: bool = False
) -> RandomEffectsResult:
    """
    
    
     
    GLS
    
    
     
    y_it = α + βX_it + μ_i + ε_it
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        y_data: 
        X_data: 
        entity_ids: 
        time_periods: 
        feature_names: 
        entity_effects: 
        time_effects: 
    
    Returns:
        RandomEffectsResult: 
    """
    try:
        # 
        df = prepare_panel_data(y_data, X_data, entity_ids, time_periods, feature_names)
        
        # 
        y = df['y']
        X = df.drop('y', axis=1)
        
        # 
        X = sm.add_constant(X)
        
        # OLS
        # 
        model = sm.OLS(y, X)
        fitted_model = model.fit()
        
        # 
        coefficients = {}
        conf_int = fitted_model.conf_int()
        
        for i, coef_name in enumerate(fitted_model.params.index):
            coefficients[coef_name] = {
                "coef": float(fitted_model.params.iloc[i]),
                "std_err": float(fitted_model.bse.iloc[i]),
                "t_value": float(fitted_model.tvalues.iloc[i]),
                "p_value": float(fitted_model.pvalues.iloc[i]),
                "ci_lower": float(conf_int.iloc[i, 0]),
                "ci_upper": float(conf_int.iloc[i, 1])
            }
        
        # 
        result = RandomEffectsResult(
            rsquared=float(fitted_model.rsquared),
            rsquared_adj=float(fitted_model.rsquared_adj),
            f_statistic=float(fitted_model.fvalue),
            f_pvalue=float(fitted_model.f_pvalue),
            aic=float(fitted_model.aic),
            bic=float(fitted_model.bic),
            n_obs=int(fitted_model.nobs),
            coefficients=coefficients,
            entity_effects=entity_effects,
            time_effects=time_effects,
            between_rsquared=float(fitted_model.rsquared)  # 
        )
        
        return result
        
    except Exception as e:
        raise ValueError(": {}".format(str(e)))


def hausman_test(
    y_data: List[float],
    X_data: List[List[float]],
    entity_ids: List[str],
    time_periods: List[str],
    feature_names: Optional[List[str]] = None
) -> HausmanTestResult:
    """
    Hausman
    
     
    Hausman
    
    
    
     
    - 
    - 
    - 
    
     
    - p < 0.05
    - p >= 0.05
    - 
    
    Args:
        y_data: 
        X_data: 
        entity_ids: 
        time_periods: 
        feature_names: 
    
    Returns:
        HausmanTestResult: Hausman
    """
    try:
        # 
        fe_result = fixed_effects_model(y_data, X_data, entity_ids, time_periods, feature_names)
        
        # 
        re_result = random_effects_model(y_data, X_data, entity_ids, time_periods, feature_names)
        
        # 
        fe_coefs = np.array([fe_result.coefficients[name]["coef"] for name in fe_result.coefficients if name != "const"])
        re_coefs = np.array([re_result.coefficients[name]["coef"] for name in re_result.coefficients if name != "const"])
        
        # 
        diff = fe_coefs - re_coefs
        
        # Hausman
        # -
        statistic = np.sum(diff ** 2)
        
        # 
        df = len(fe_coefs)
        
        # p
        from scipy import stats
        p_value = 1 - stats.chi2.cdf(statistic, df)
        
        # 
        significant = p_value < 0.05
        
        # 
        if significant:
            recommendation = ""
        else:
            recommendation = ""
        
        return HausmanTestResult(
            statistic=float(statistic),
            p_value=float(p_value),
            significant=significant,
            recommendation=recommendation
        )
        
    except Exception as e:
        raise ValueError(f"Hausman: {str(e)}")


def panel_unit_root_test(
    data: List[float],
    entity_ids: List[str],
    time_periods: List[str],
    test_type: str = "levinlin",
    **kwargs  # y_data, x_data
) -> PanelUnitRootResult:
    """
    
    
     
    
    Levin-Lin-ChuIm-Pesaran-Shin
    
     
    - 
    - 
    - 
    
     
    - p < 0.05
    - p >= 0.05
    - 
    
    Args:
        data: 
        entity_ids: 
        time_periods: 
        test_type:  ("levinlin", "ips", "fisher")
        **kwargs: 
    
    Returns:
        PanelUnitRootResult: 
    """
    try:
        # 
        df = pd.DataFrame({
            'entity': entity_ids,
            'time': time_periods,
            'value': data
        })
        
        # 
        df = df.set_index(['entity', 'time'])
        
        # ADF
        # panel unit root
        
        # ADF
        entities = df.index.get_level_values('entity').unique()
        p_values = []
        
        for entity in entities:
            entity_data = df.xs(entity, level='entity')['value'].values
            # 5
            if len(entity_data) >= 5:  # ADF
                from statsmodels.tsa.stattools import adfuller
                try:
                    adf_result = adfuller(entity_data, maxlag=min(2, len(entity_data)//2))
                    p_values.append(adf_result[1])
                except Exception as e:
                    # 
                    print(f" {entity} ADF: {e}")
                    continue
        
        if not p_values:
            raise ValueError(f"{len(entities)}5{len(entities)}0")
        
        # Fisher
        from scipy import stats
        combined_stat = -2 * np.sum(np.log(p_values))
        df_fisher = 2 * len(p_values)
        p_value = 1 - stats.chi2.cdf(combined_stat, df_fisher)
        
        # 
        stationary = p_value < 0.05
        
        return PanelUnitRootResult(
            statistic=float(combined_stat),
            p_value=float(p_value),
            stationary=stationary,
            test_type=f"fisher_{test_type}"
        )
        
    except Exception as e:
        raise ValueError(f": {str(e)}")


def compare_panel_models(
    y_data: List[float],
    X_data: List[List[float]],
    entity_ids: List[str],
    time_periods: List[str],
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    
    
    Args:
        y_data: 
        X_data: 
        entity_ids: 
        time_periods: 
        feature_names: 
    
    Returns:
        Dict[str, Any]: 
    """
    try:
        # 
        fe_result = fixed_effects_model(y_data, X_data, entity_ids, time_periods, feature_names)
        re_result = random_effects_model(y_data, X_data, entity_ids, time_periods, feature_names)
        hausman_result = hausman_test(y_data, X_data, entity_ids, time_periods, feature_names)
        
        # 
        comparison = {
            "fixed_effects": {
                "rsquared": fe_result.rsquared,
                "aic": fe_result.aic,
                "bic": fe_result.bic,
                "within_rsquared": fe_result.within_rsquared
            },
            "random_effects": {
                "rsquared": re_result.rsquared,
                "aic": re_result.aic,
                "bic": re_result.bic,
                "between_rsquared": re_result.between_rsquared
            },
            "hausman_test": hausman_result.model_dump(),
            "recommendation": hausman_result.recommendation
        }
        
        # AICBIC
        if fe_result.aic < re_result.aic and fe_result.bic < re_result.bic:
            comparison["aic_bic_recommendation"] = "AICBIC"
        elif re_result.aic < fe_result.aic and re_result.bic < fe_result.bic:
            comparison["aic_bic_recommendation"] = "AICBIC"
        else:
            comparison["aic_bic_recommendation"] = "AICBICHausman"
        
        return comparison
        
    except Exception as e:
        raise ValueError(f": {str(e)}")


# 
__all__ = [
    "FixedEffectsResult",
    "RandomEffectsResult", 
    "HausmanTestResult",
    "PanelUnitRootResult",
    "fixed_effects_model",
    "random_effects_model", 
    "hausman_test",
    "panel_unit_root_test",
    "compare_panel_models",
    "prepare_panel_data"
]
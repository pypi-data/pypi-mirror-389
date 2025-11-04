# -*- coding: utf-8 -*-
"""


"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa import stattools
from scipy import stats
from typing import Dict, List, Any, Optional
from mcp.types import CallToolResult, TextContent

from .statistics import calculate_descriptive_stats, calculate_correlation_matrix, perform_hypothesis_test
from .regression import perform_ols_regression
from .panel_data import fixed_effects_model, random_effects_model, hausman_test, panel_unit_root_test
from .time_series import var_model, vecm_model, garch_model, state_space_model, variance_decomposition
from .machine_learning import (
    random_forest_regression, gradient_boosting_regression,
    lasso_regression, ridge_regression, cross_validation, feature_importance_analysis
)
from .timeout import with_timeout, TimeoutError


async def handle_descriptive_statistics(ctx, data: Dict[str, List[float]], **kwargs) -> CallToolResult:
    """"""
    if not data:
        raise ValueError("")
    
    df = pd.DataFrame(data)
    
    # 
    result_data = {
        "count": len(df),
        "mean": float(df.mean().mean()),
        "std": float(df.std().mean()),
        "min": float(df.min().min()),
        "max": float(df.max().max()),
        "median": float(df.median().mean()),
        "skewness": float(df.skew().mean()),
        "kurtosis": float(df.kurtosis().mean())
    }
    
    correlation_matrix = df.corr().round(4)
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"\n"
                     f": {result_data['mean']:.4f}\n"
                     f": {result_data['std']:.4f}\n"
                     f": {result_data['min']:.4f}\n"
                     f": {result_data['max']:.4f}\n"
                     f": {result_data['median']:.4f}\n"
                     f": {result_data['skewness']:.4f}\n"
                     f": {result_data['kurtosis']:.4f}\n\n"
                     f"\n{correlation_matrix.to_string()}"
            )
        ],
        structuredContent=result_data
    )


async def handle_ols_regression(ctx, y_data: List[float], x_data: List[List[float]], 
                                feature_names: Optional[List[str]] = None, **kwargs) -> CallToolResult:
    """OLS"""
    if not y_data or not x_data:
        raise ValueError("")
    
    X = np.array(x_data)
    y = np.array(y_data)
    X_with_const = sm.add_constant(X)
    model = sm.OLS(y, X_with_const).fit()
    
    if feature_names is None:
        feature_names = [f"x{i+1}" for i in range(X.shape[1])]
    
    conf_int = model.conf_int()
    coefficients = {}
    
    for i, coef in enumerate(model.params):
        var_name = "const" if i == 0 else feature_names[i-1]
        coefficients[var_name] = {
            "coef": float(coef),
            "std_err": float(model.bse[i]),
            "t_value": float(model.tvalues[i]),
            "p_value": float(model.pvalues[i]),
            "ci_lower": float(conf_int[i][0]),
            "ci_upper": float(conf_int[i][1])
        }
    
    result_data = {
        "rsquared": float(model.rsquared),
        "rsquared_adj": float(model.rsquared_adj),
        "f_statistic": float(model.fvalue),
        "f_pvalue": float(model.f_pvalue),
        "aic": float(model.aic),
        "bic": float(model.bic),
        "coefficients": coefficients
    }
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"OLS\n"
                     f"R² = {result_data['rsquared']:.4f}\n"
                     f"R² = {result_data['rsquared_adj']:.4f}\n"
                     f"F = {result_data['f_statistic']:.4f} (p = {result_data['f_pvalue']:.4f})\n"
                     f"AIC = {result_data['aic']:.2f}, BIC = {result_data['bic']:.2f}\n\n"
                     f"\n{model.summary().tables[1]}"
            )
        ],
        structuredContent=result_data
    )


async def handle_hypothesis_testing(ctx, data1: List[float], data2: Optional[List[float]] = None,
                                    test_type: str = "t_test", **kwargs) -> CallToolResult:
    """"""
    if test_type == "t_test":
        if data2 is None:
            result = stats.ttest_1samp(data1, 0)
            ci = stats.t.interval(0.95, len(data1)-1, loc=np.mean(data1), scale=stats.sem(data1))
        else:
            result = stats.ttest_ind(data1, data2)
            ci = None
        
        test_result = {
            "test_type": test_type,
            "statistic": float(result.statistic),
            "p_value": float(result.pvalue),
            "significant": bool(result.pvalue < 0.05),
            "confidence_interval": list(ci) if ci else None
        }
    elif test_type == "adf":
        result = stattools.adfuller(data1)
        test_result = {
            "test_type": "adf",
            "statistic": float(result[0]),
            "p_value": float(result[1]),
            "significant": bool(result[1] < 0.05),
            "confidence_interval": None
        }
    else:
        raise ValueError(f": {test_type}")
    
    ci_text = ""
    if test_result['confidence_interval']:
        ci_lower = test_result['confidence_interval'][0]
        ci_upper = test_result['confidence_interval'][1]
        ci_text = f"95%: [{ci_lower:.4f}, {ci_upper:.4f}]"
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"{test_type.upper()}\n"
                     f" = {test_result['statistic']:.4f}\n"
                     f"p = {test_result['p_value']:.4f}\n"
                     f"{'' if test_result['significant'] else ''} (5%)\n"
                     f"{ci_text}"
            )
        ],
        structuredContent=test_result
    )


async def handle_time_series_analysis(ctx, data: List[float], **kwargs) -> CallToolResult:
    """ - """
    if not data or len(data) < 5:
        raise ValueError("5")
    
    # 
    original_length = len(data)
    max_data_points = 1000  # 
    
    # 
    if original_length > max_data_points:
        # 
        step = original_length // max_data_points
        data = data[::step]
    
    series = pd.Series(data)
    
    # 
    try:
        basic_stats = {
            "count": original_length,  # 
            "mean": float(series.mean()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "median": float(series.median()),
            "skewness": float(series.skew()),
            "kurtosis": float(series.kurtosis()),
            "variance": float(series.var()),
            "range": float(series.max() - series.min()),
            "cv": float(series.std() / series.mean()) if series.mean() != 0 else 0
        }
    except Exception as e:
        raise ValueError(f": {str(e)}")
    
    # 
    try:
        adf_result = stattools.adfuller(data, maxlag=min(12, len(data)//5))
    except Exception as e:
        # 
        adf_result = (0.0, 0.5, 0, len(data)-1, {}, 0.0)
    
    try:
        kpss_result = stattools.kpss(data, regression='c', nlags=min(12, len(data)//5))
    except Exception as e:
        # 
        kpss_result = (0.0, 0.5, 0, {})
    
    # 
    max_nlags = min(15, len(data) // 3, 40)  # 
    if max_nlags < 1:
        max_nlags = 1
    
    try:
        acf_values = stattools.acf(data, nlags=max_nlags, fft=True)  # FFT
        pacf_values = stattools.pacf(data, nlags=max_nlags, method='ywm')  # 
    except Exception as e:
        # 
        acf_values = np.zeros(max_nlags + 1)
        pacf_values = np.zeros(max_nlags + 1)
        acf_values[0] = pacf_values[0] = 1.0
    
    # 
    try:
        if len(data) > 1:
            trend_strength = abs(np.corrcoef(range(len(data)), data)[0, 1])
        else:
            trend_strength = 0.0
    except:
        trend_strength = 0.0
    
    # 
    seasonal_pattern = False
    if 12 <= len(data) <= 500:  # 
        try:
            seasonal_lag = min(12, len(data)//3)
            seasonal_acf = stattools.acf(data, nlags=seasonal_lag, fft=True)
            seasonal_pattern = any(abs(x) > 0.3 for x in seasonal_acf[1:])
        except:
            seasonal_pattern = False
    
    # 
    sampling_notice = ""
    if original_length > max_data_points:
        sampling_notice = f"\n ({original_length}){len(data)}\n"
    
    result_text = f""" {sampling_notice}

 
-  = {basic_stats['count']}
-  = {basic_stats['mean']:.4f}
-  = {basic_stats['std']:.4f}
-  = {basic_stats['variance']:.4f}
-  = {basic_stats['min']:.4f}
-  = {basic_stats['max']:.4f}
-  = {basic_stats['range']:.4f}
-  = {basic_stats['median']:.4f}
-  = {basic_stats['skewness']:.4f}
-  = {basic_stats['kurtosis']:.4f}
-  = {basic_stats['cv']:.4f}

 
- ADF = {adf_result[0]:.4f}
- ADFp = {adf_result[1]:.4f}
- KPSS = {kpss_result[0]:.4f}
- KPSSp = {kpss_result[1]:.4f}
-  = {'' if adf_result[1] < 0.05 and kpss_result[1] > 0.05 else ''}

 
- ACF5: {[f'{x:.4f}' for x in acf_values[:min(5, len(acf_values))]]}
- PACF5: {[f'{x:.4f}' for x in pacf_values[:min(5, len(pacf_values))]]}
- : {max(abs(acf_values[1:])) if len(acf_values) > 1 else 0:.4f}
- : {max(abs(pacf_values[1:])) if len(pacf_values) > 1 else 0:.4f}

 
- : {trend_strength:.4f}
- : {'' if seasonal_pattern else ''}
- : {'' if basic_stats['cv'] > 0.5 else '' if basic_stats['cv'] > 0.2 else ''}
- : {'' if basic_stats['skewness'] > 0.5 else '' if basic_stats['skewness'] < -0.5 else ''}
- : {'' if basic_stats['kurtosis'] > 3 else '' if basic_stats['kurtosis'] < 3 else ''}"""

    # 
    result_text += f"\n\n "
    
    if adf_result[1] < 0.05:  # 
        result_text += f"\n- "
        
        # ACF/PACF
        acf_decay = abs(acf_values[1]) > 0.5
        pacf_cutoff = abs(pacf_values[1]) > 0.5 and all(abs(x) < 0.3 for x in pacf_values[2:5])
        
        if acf_decay and pacf_cutoff:
            result_text += f"\n- ACFPACF1AR(1)"
            result_text += f"\n- ARMA(1,1)"
        elif not acf_decay and pacf_cutoff:
            result_text += f"\n- ACFPACFMA"
        elif acf_decay and not pacf_cutoff:
            result_text += f"\n- ACFPACFAR"
        else:
            result_text += f"\n- ACFPACFARMA"
            
        # 
        if seasonal_pattern:
            result_text += f"\n- SARIMA"
        if trend_strength > 0.7:
            result_text += f"\n- "
            
    else:  # 
        result_text += f"\n- "
        result_text += f"\n- ARIMA(p,d,q)d"
        
        # 
        if trend_strength > 0.8:
            result_text += f"\n- 1-2"
        elif trend_strength > 0.5:
            result_text += f"\n- 1"
        else:
            result_text += f"\n- 1"
            
        if seasonal_pattern:
            result_text += f"\n- SARIMA"
    
    # 
    if len(data) < 30:
        result_text += f"\n- ({len(data)})"
    elif len(data) < 100:
        result_text += f"\n- ({len(data)})"
    else:
        result_text += f"\n- ({len(data)})"
    
    result_text += f"\n\n "
    result_text += f"\n- "
    result_text += f"\n- ACFPACF"
    result_text += f"\n- AIC/BIC"
    result_text += f"\n- "
    result_text += f"\n- "
    result_text += f"\n- "
    
    result_data = {
        "basic_statistics": basic_stats,
        "adf_statistic": float(adf_result[0]),
        "adf_pvalue": float(adf_result[1]),
        "kpss_statistic": float(kpss_result[0]),
        "kpss_pvalue": float(kpss_result[1]),
        "stationary": bool(adf_result[1] < 0.05 and kpss_result[1] > 0.05),
        "acf": [float(x) for x in acf_values.tolist()],
        "pacf": [float(x) for x in pacf_values.tolist()],
        "diagnostic_stats": {
            "trend_strength": trend_strength,
            "seasonal_pattern": seasonal_pattern,
            "volatility_level": "high" if basic_stats['cv'] > 0.5 else "medium" if basic_stats['cv'] > 0.2 else "low",
            "distribution_shape": "right_skewed" if basic_stats['skewness'] > 0.5 else "left_skewed" if basic_stats['skewness'] < -0.5 else "symmetric",
            "kurtosis_type": "leptokurtic" if basic_stats['kurtosis'] > 3 else "platykurtic" if basic_stats['kurtosis'] < 3 else "mesokurtic"
        },
        "model_suggestions": {
            "is_stationary": adf_result[1] < 0.05,
            "suggested_models": ["ARMA", "ARIMA"] if adf_result[1] < 0.05 else ["ARIMA", "SARIMA"],
            "data_sufficiency": "low" if len(data) < 30 else "medium" if len(data) < 100 else "high",
            "trend_recommendation": "strong_diff" if trend_strength > 0.8 else "moderate_diff" if trend_strength > 0.5 else "weak_diff",
            "seasonal_recommendation": "consider_seasonal" if seasonal_pattern else "no_seasonal"
        }
    }
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result_data
    )


async def handle_correlation_analysis(ctx, data: Dict[str, List[float]], 
                                     method: str = "pearson", **kwargs) -> CallToolResult:
    """"""
    if not data or len(data) < 2:
        raise ValueError("2")
    
    df = pd.DataFrame(data)
    correlation_matrix = df.corr(method=method)
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"{method.title()}\n{correlation_matrix.round(4).to_string()}"
            )
        ]
    )


# 
async def handle_panel_fixed_effects(ctx, y_data, x_data, entity_ids, time_periods,
                                    feature_names=None, entity_effects=True, time_effects=False, **kwargs):
    """ - """
    result = fixed_effects_model(y_data, x_data, entity_ids, time_periods, feature_names, entity_effects, time_effects)
    
    # 
    result_text = f""" 

 
- R² = {result.rsquared:.4f}
- R² = {result.rsquared_adj:.4f}
- F = {result.f_statistic:.4f} (p = {result.f_pvalue:.4f})
- AIC = {result.aic:.2f}, BIC = {result.bic:.2f}
-  = {result.n_obs}
-  = {'' if result.entity_effects else ''}
-  = {'' if result.time_effects else ''}

 """
    
    # 
    for var_name, coef_info in result.coefficients.items():
        significance = "***" if coef_info["p_value"] < 0.01 else "**" if coef_info["p_value"] < 0.05 else "*" if coef_info["p_value"] < 0.1 else ""
        result_text += f"\n- {var_name}: {coef_info['coef']:.4f}{significance} (se={coef_info['std_err']:.4f}, p={coef_info['p_value']:.4f})"
    
    result_text += "\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_panel_random_effects(ctx, y_data, x_data, entity_ids, time_periods,
                                     feature_names=None, entity_effects=True, time_effects=False, **kwargs):
    """ - """
    result = random_effects_model(y_data, x_data, entity_ids, time_periods, feature_names, entity_effects, time_effects)
    
    # 
    result_text = f""" 

 
- R² = {result.rsquared:.4f}
- R² = {result.rsquared_adj:.4f}
- F = {result.f_statistic:.4f} (p = {result.f_pvalue:.4f})
- AIC = {result.aic:.2f}, BIC = {result.bic:.2f}
-  = {result.n_obs}
-  = {'' if result.entity_effects else ''}
-  = {'' if result.time_effects else ''}

 """
    
    # 
    for var_name, coef_info in result.coefficients.items():
        significance = "***" if coef_info["p_value"] < 0.01 else "**" if coef_info["p_value"] < 0.05 else "*" if coef_info["p_value"] < 0.1 else ""
        result_text += f"\n- {var_name}: {coef_info['coef']:.4f}{significance} (se={coef_info['std_err']:.4f}, p={coef_info['p_value']:.4f})"
    
    result_text += "\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_panel_hausman_test(ctx, y_data, x_data, entity_ids, time_periods, feature_names=None, **kwargs):
    """Hausman - """
    result = hausman_test(y_data, x_data, entity_ids, time_periods, feature_names)
    
    result_text = f""" Hausman

 
-  = {result.statistic:.4f}
- p = {result.p_value:.4f}
-  = {'' if result.significant else ''} (5%)

 
{result.recommendation}

 
- p < 0.05: 
- p >= 0.05: 

 Hausman"""
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_panel_unit_root_test(ctx, **kwargs):
    """
     - 
    
    panel_unit_root_testdata, entity_ids, time_periods
    panely_data, x_data, entity_ids, time_periods
    """
    # 
    data = kwargs.get('data')
    y_data = kwargs.get('y_data')
    entity_ids = kwargs.get('entity_ids')
    time_periods = kwargs.get('time_periods')
    test_type = kwargs.get('test_type', 'levinlin')
    
    # datay_datay_datapanel
    if data is None and y_data is not None:
        data = y_data
    
    if data is None:
        raise ValueError("datay_data")
    
    if entity_ids is None or time_periods is None:
        raise ValueError("entity_idstime_periods")
    
    # panel_unit_root_test
    result = panel_unit_root_test(data, entity_ids, time_periods, test_type)
    
    # 
    result_text = f""" 

 
-  = {test_type.upper()}
-  = {len(set(entity_ids))}
-  = {len(set(time_periods))}
-  = {result.statistic:.4f}
- p = {result.p_value:.4f}
-  = {'' if result.stationary else ''} (5%)

 """
    
    # 
    if hasattr(result, 'critical_values'):
        result_text += f"\n- : {result.critical_values}"
    if hasattr(result, 'lags_used'):
        result_text += f"\n- : {result.lags_used}"
    if hasattr(result, 'test_statistic'):
        result_text += f"\n- : {result.test_statistic:.4f}"
    
    result_text += f"\n\n "
    result_text += f"\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


# 
@with_timeout(seconds=60)
async def handle_var_model(ctx, data, max_lags=5, ic="aic", **kwargs):
    """VAR - """
    try:
        result = var_model(data, max_lags=max_lags, ic=ic)
    except TimeoutError:
        raise TimeoutError("VAR60")
    
    # 
    result_text = f""" VAR

 
-  = {result.order}
-  = {len(result.variables) if hasattr(result, 'variables') else ''}
-  = {ic.upper()}
- AIC = {result.aic:.2f}
- BIC = {getattr(result, 'bic', 'N/A')}
- HQIC = {getattr(result, 'hqic', 'N/A')}

 """
    
    # 
    if hasattr(result, 'residuals_normality'):
        result_text += f"\n- : {result.residuals_normality}"
    if hasattr(result, 'serial_correlation'):
        result_text += f"\n- : {result.serial_correlation}"
    if hasattr(result, 'stability'):
        result_text += f"\n- : {result.stability}"
    
    # 
    if hasattr(result, 'variables'):
        result_text += f"\n\n "
        for var in result.variables:
            result_text += f"\n- {var}"
    
    result_text += f"\n\n VAR"
    result_text += f"\n\n VAR"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


@with_timeout(seconds=60)
async def handle_vecm_model(ctx, data, coint_rank=1, deterministic="co", max_lags=5, **kwargs):
    """VECM - """
    try:
        result = vecm_model(data, coint_rank=coint_rank, deterministic=deterministic, max_lags=max_lags)
    except TimeoutError:
        raise TimeoutError("VECM60")
    
    # 
    result_text = f""" VECM

 
-  = {result.coint_rank}
-  = {deterministic}
-  = {max_lags}
- AIC = {result.aic:.2f}
- BIC = {getattr(result, 'bic', 'N/A')}
- HQIC = {getattr(result, 'hqic', 'N/A')}

 """
    
    # 
    if hasattr(result, 'coint_relations'):
        result_text += f"\n- : {len(result.coint_relations)}"
        for i, relation in enumerate(result.coint_relations[:3], 1):  # 3
            result_text += f"\n- {i}: {relation}"
        if len(result.coint_relations) > 3:
            result_text += f"\n- ... {len(result.coint_relations) - 3}"
    
    # 
    if hasattr(result, 'error_correction'):
        result_text += f"\n\n "
        result_text += f"\n- : {result.error_correction}"
    
    result_text += f"\n\n VECM"
    result_text += f"\n\n VECM"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


@with_timeout(seconds=30)
async def handle_garch_model(ctx, data, order=(1, 1), dist="normal", **kwargs):
    """GARCH - """
    try:
        result = garch_model(data, order=order, dist=dist)
    except TimeoutError:
        raise TimeoutError("GARCH30")
    
    # 
    result_text = f""" GARCH

 
- GARCH = ({order[0]}, {order[1]})
-  = {dist}
-  = {result.persistence:.4f}
- AIC = {result.aic:.2f}
- BIC = {getattr(result, 'bic', 'N/A')}

 """
    
    # 
    if hasattr(result, 'volatility_persistence'):
        result_text += f"\n- : {result.volatility_persistence:.4f}"
    if hasattr(result, 'unconditional_variance'):
        result_text += f"\n- : {result.unconditional_variance:.4f}"
    if hasattr(result, 'leverage_effect'):
        result_text += f"\n- : {result.leverage_effect}"
    
    # 
    if hasattr(result, 'residuals_test'):
        result_text += f"\n\n "
        result_text += f"\n- : {result.residuals_test}"
    
    result_text += f"\n\n GARCH"
    result_text += f"\n\n GARCH"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


@with_timeout(seconds=45)
async def handle_state_space_model(ctx, data, state_dim=1, observation_dim=1,
                                  trend=True, seasonal=False, period=12, **kwargs):
    """ - """
    try:
        result = state_space_model(data, state_dim, observation_dim, trend, seasonal, period)
    except TimeoutError:
        raise TimeoutError("45")
    
    # 
    result_text = f""" 

 
-  = {state_dim}
-  = {observation_dim}
-  = {'' if trend else ''}
-  = {'' if seasonal else ''}
-  = {period if seasonal else 'N/A'}
- AIC = {result.aic:.2f}
- BIC = {result.bic:.2f}
-  = {result.log_likelihood:.2f}

 """

    # 
    if result.state_names:
        result_text += f"\n- : {', '.join(result.state_names)}"
    if result.observation_names:
        result_text += f"\n- : {', '.join(result.observation_names)}"
    
    # 
    if result.filtered_state:
        result_text += f"\n- : "
    if result.smoothed_state:
        result_text += f"\n- : "

    result_text += f"\n\n "
    result_text += f"\n\n "

    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


@with_timeout(seconds=30)
async def handle_variance_decomposition(ctx, data, periods=10, max_lags=5, **kwargs):
    """ - """
    try:
        result = variance_decomposition(data, periods=periods, max_lags=max_lags)
    except TimeoutError:
        raise TimeoutError("30")
    
    # 
    result_text = f""" 

 
-  = {periods}
-  = {max_lags}
-  = {len(data) if data else ''}

 """

    # 
    if isinstance(result, dict) and "variance_decomposition" in result:
        variance_decomp = result["variance_decomposition"]
        horizon = result.get("horizon", periods)
        
        result_text += f"\n- : {horizon}"
        
        for var_name, decomposition in variance_decomp.items():
            result_text += f"\n\n  '{var_name}' "
            if isinstance(decomposition, dict):
                for source, percentages in decomposition.items():
                    if isinstance(percentages, list) and len(percentages) > 0:
                        # 
                        final_percentage = percentages[-1] * 100 if isinstance(percentages[-1], (int, float)) else 0
                        result_text += f"\n- {source}: {final_percentage:.1f}%"
                    else:
                        result_text += f"\n- {source}: {percentages:.1f}%"
            else:
                result_text += f"\n- : {decomposition:.1f}%"
    else:
        result_text += f"\n- "

    result_text += f"\n\n "
    result_text += f"\n\n VAR"

    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result
    )


# 
async def handle_random_forest(ctx, y_data, x_data, feature_names=None, n_estimators=100, max_depth=None, **kwargs):
    """ - """
    result = random_forest_regression(y_data, x_data, feature_names, n_estimators, max_depth)
    
    # R²
    r2_warning = ""
    if result.r2_score < 0:
        r2_warning = f"\n R²({result.r2_score:.4f})1)  2)  3) "
    
    # 
    result_text = f""" 

 
- R² = {result.r2_score:.4f}
- (MSE) = {result.mse:.4f}
- (MAE) = {result.mae:.4f}
-  = {result.n_obs}
-  = {result.n_estimators}
-  = {result.max_depth if result.max_depth else ''}
-  = {f"{result.oob_score:.4f}" if result.oob_score else ''}
{r2_warning}

 10"""
    
    # 
    if result.feature_importance:
        sorted_features = sorted(result.feature_importance.items(), key=lambda x: x[1], reverse=True)
        for i, (feature, importance) in enumerate(sorted_features[:10]):
            result_text += f"\n- {feature}: {importance:.4f}"
        if len(sorted_features) > 10:
            result_text += f"\n- ... {len(sorted_features) - 10}"
    else:
        result_text += "\n- "
    
    result_text += f"\n\n "
    result_text += f"\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_gradient_boosting(ctx, y_data, x_data, feature_names=None,
                                  n_estimators=100, learning_rate=0.1, max_depth=3, **kwargs):
    """ - """
    result = gradient_boosting_regression(y_data, x_data, feature_names, n_estimators, learning_rate, max_depth)
    
    # R²
    r2_warning = ""
    if result.r2_score < 0:
        r2_warning = f"\n R²({result.r2_score:.4f})1)  2)  3) "
    
    # 
    result_text = f""" 

 
- R² = {result.r2_score:.4f}
- (MSE) = {result.mse:.4f}
- (MAE) = {result.mae:.4f}
-  = {result.n_obs}
-  = {result.n_estimators}
-  = {result.learning_rate}
-  = {result.max_depth}
{r2_warning}

 10"""
    
    # 
    if result.feature_importance:
        sorted_features = sorted(result.feature_importance.items(), key=lambda x: x[1], reverse=True)
        for i, (feature, importance) in enumerate(sorted_features[:10]):
            result_text += f"\n- {feature}: {importance:.4f}"
        if len(sorted_features) > 10:
            result_text += f"\n- ... {len(sorted_features) - 10}"
    else:
        result_text += "\n- "
    
    result_text += f"\n\n "
    result_text += f"\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_lasso_regression(ctx, y_data, x_data, feature_names=None, alpha=1.0, **kwargs):
    """Lasso - """
    result = lasso_regression(y_data, x_data, feature_names, alpha)
    
    # R²
    r2_warning = ""
    if result.r2_score < 0:
        r2_warning = f"\n R²({result.r2_score:.4f})1)  2) alpha 3) "
    
    # 0
    coef_warning = ""
    if all(abs(coef) < 1e-10 for coef in result.coefficients.values()):
        coef_warning = f"\n 0alpha={alpha}alpha"
    
    # 
    result_text = f""" Lasso

 
- R² = {result.r2_score:.4f}
- (MSE) = {result.mse:.4f}
- (MAE) = {result.mae:.4f}
-  = {result.n_obs}
- (alpha) = {result.alpha}
{r2_warning}{coef_warning}

 """
    
    # 
    sorted_coefficients = sorted(result.coefficients.items(), key=lambda x: abs(x[1]), reverse=True)
    for var_name, coef in sorted_coefficients:
        if abs(coef) > 1e-10:  # 
            result_text += f"\n- {var_name}: {coef:.4f}"
        else:
            result_text += f"\n- {var_name}: 0.0000 ()"
    
    result_text += f"\n\n LassoL10"
    result_text += f"\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_ridge_regression(ctx, y_data, x_data, feature_names=None, alpha=1.0, **kwargs):
    """Ridge - """
    result = ridge_regression(y_data, x_data, feature_names, alpha)
    
    # R²
    r2_warning = ""
    if result.r2_score < 0:
        r2_warning = f"\n R²({result.r2_score:.4f})1)  2) alpha 3) "
    
    # 
    result_text = f""" Ridge

 
- R² = {result.r2_score:.4f}
- (MSE) = {result.mse:.4f}
- (MAE) = {result.mae:.4f}
-  = {result.n_obs}
- (alpha) = {result.alpha}
{r2_warning}

 """
    
    # 
    sorted_coefficients = sorted(result.coefficients.items(), key=lambda x: abs(x[1]), reverse=True)
    for var_name, coef in sorted_coefficients:
        result_text += f"\n- {var_name}: {coef:.4f}"
    
    result_text += f"\n\n RidgeL2"
    result_text += f"\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_cross_validation(ctx, y_data, x_data, model_type="random_forest", cv_folds=5, scoring="r2", **kwargs):
    """ - """
    result = cross_validation(y_data, x_data, model_type, cv_folds, scoring)
    
    # 
    result_text = f""" 

 
-  = {result.model_type}
-  = {result.n_splits}
-  = {scoring}
-  = {result.mean_score:.4f}
-  = {result.std_score:.4f}
-  = {(result.std_score / abs(result.mean_score)) * 100 if result.mean_score != 0 else 0:.2f}%

 """
    
    # 
    for i, score in enumerate(result.cv_scores, 1):
        result_text += f"\n- {i}: {score:.4f}"
    
    # 
    stability_assessment = ""
    cv_threshold = 0.1  # 10%
    cv_value = (result.std_score / abs(result.mean_score)) if result.mean_score != 0 else 0
    
    if cv_value < cv_threshold:
        stability_assessment = f"\n\n {cv_value*100:.2f}% < {cv_threshold*100:.0f}%"
    elif cv_value < cv_threshold * 2:
        stability_assessment = f"\n\n {cv_value*100:.2f}% {cv_threshold*100:.0f}%-{cv_threshold*2*100:.0f}%"
    else:
        stability_assessment = f"\n\n {cv_value*100:.2f}% > {cv_threshold*2*100:.0f}%"
    
    result_text += stability_assessment
    result_text += f"\n\n "
    result_text += f"\n\n 10%"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_feature_importance(ctx, y_data, x_data, feature_names=None, method="random_forest", top_k=5, **kwargs):
    """ - """
    result = feature_importance_analysis(y_data, x_data, feature_names, method, top_k)
    
    # 
    result_text = f""" 

 
-  = {method}
- Top = {top_k}
-  = {len(result.feature_importance)}

 """
    
    # 
    for i, (feature, importance) in enumerate(result.sorted_features[:top_k], 1):
        percentage = (importance / sum(result.feature_importance.values())) * 100 if sum(result.feature_importance.values()) > 0 else 0
        result_text += f"\n{i}. {feature}: {importance:.4f} ({percentage:.1f}%)"
    
    # 
    if len(result.sorted_features) > 0:
        top_k_importance = sum(imp for _, imp in result.sorted_features[:top_k])
        total_importance = sum(result.feature_importance.values())
        top_k_percentage = (top_k_importance / total_importance) * 100 if total_importance > 0 else 0
        
        result_text += f"\n\n "
        result_text += f"\n- Top {top_k}: {top_k_percentage:.1f}%"
        result_text += f"\n- : {100 - top_k_percentage:.1f}%"
    
    result_text += f"\n\n "
    result_text += f"\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


# ============================================================================
#  ()
# ============================================================================

async def handle_logit_regression(ctx, y_data, x_data, feature_names=None, **kwargs):
    """Logit"""
    from .discrete_choice import logit_model
    
    result = logit_model(y_data, x_data, feature_names)
    
    result_text = f""" Logit

 
- R² = {result.pseudo_rsquared:.4f}
- AIC = {result.aic:.2f}
- BIC = {result.bic:.2f}
-  = {result.log_likelihood:.2f}
-  = {result.n_obs}

 """
    
    for var_name, coef_info in result.coefficients.items():
        sig = "***" if coef_info["p_value"] < 0.01 else "**" if coef_info["p_value"] < 0.05 else "*" if coef_info["p_value"] < 0.1 else ""
        result_text += f"\n- {var_name}: {coef_info['coefficient']:.4f}{sig} (OR={coef_info['odds_ratio']:.4f}, se={coef_info['std_error']:.4f}, p={coef_info['p_value']:.4f})"
    
    result_text += "\n\n LogitOdds Ratio>1"
    result_text += "\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_probit_regression(ctx, y_data, x_data, feature_names=None, **kwargs):
    """Probit"""
    from .discrete_choice import probit_model
    
    result = probit_model(y_data, x_data, feature_names)
    
    result_text = f""" Probit

 
- R² = {result.pseudo_rsquared:.4f}
- AIC = {result.aic:.2f}
- BIC = {result.bic:.2f}
-  = {result.log_likelihood:.2f}
-  = {result.n_obs}

 """
    
    for var_name, coef_info in result.coefficients.items():
        sig = "***" if coef_info["p_value"] < 0.01 else "**" if coef_info["p_value"] < 0.05 else "*" if coef_info["p_value"] < 0.1 else ""
        result_text += f"\n- {var_name}: {coef_info['coefficient']:.4f}{sig} (se={coef_info['std_error']:.4f}, p={coef_info['p_value']:.4f})"
    
    result_text += "\n\n Probit"
    result_text += "\n\n ProbitLogit"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_poisson_regression(ctx, y_data, x_data, feature_names=None, **kwargs):
    """"""
    from .discrete_choice import poisson_regression
    
    result = poisson_regression(y_data, x_data, feature_names)
    
    result_text = f""" 

 
- R² = {result.pseudo_rsquared:.4f}
- AIC = {result.aic:.2f}
- BIC = {result.bic:.2f}
-  = {result.log_likelihood:.2f}
-  = {result.n_obs}
-  = {result.dispersion:.4f}

 """
    
    for var_name, coef_info in result.coefficients.items():
        sig = "***" if coef_info["p_value"] < 0.01 else "**" if coef_info["p_value"] < 0.05 else "*" if coef_info["p_value"] < 0.1 else ""
        result_text += f"\n- {var_name}: {coef_info['coefficient']:.4f}{sig} (IRR={coef_info['incidence_rate_ratio']:.4f}, se={coef_info['std_error']:.4f}, p={coef_info['p_value']:.4f})"
    
    result_text += f"\n\n "
    result_text += f"\n-  = {result.dispersion:.4f}"
    result_text += f"\n- {'' if result.dispersion > 1.5 else '' if result.dispersion < 1.2 else ''}"
    
    result_text += "\n\n (IRR)"
    result_text += "\n\n >1.5"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


# ============================================================================
#  ()
# ============================================================================

async def handle_psm(ctx, treatment, covariates, outcome, feature_names=None, caliper=0.2, **kwargs):
    """"""
    from .advanced_econometrics import propensity_score_matching
    
    result = propensity_score_matching(treatment, covariates, outcome, feature_names, caliper=caliper)
    
    result_text = f""" (PSM)

 
-  = {result.matched_sample_size}
-  = {sum(treatment)}
-  = {result.matched_sample_size / sum(treatment) * 100:.1f}%
- (Caliper) = {caliper}

 
- (ATT) = {result.treatment_effect:.4f}
-  = {result.standard_error:.4f}
- t = {result.t_statistic:.4f}
- p = {result.p_value:.4f}
- {'' if result.p_value < 0.05 else ''} (5%)

 """
    
    for var_name, diff in result.balance_metrics.items():
        result_text += f"\n- {var_name}: {diff:.4f}"
    
    result_text += "\n\n PSM"
    result_text += "\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_did(ctx, treatment, time_period, outcome, covariates=None, **kwargs):
    """"""
    from .advanced_econometrics import difference_in_differences
    
    result = difference_in_differences(treatment, time_period, outcome, covariates)
    
    result_text = f""" (DID)

 DID
- DID = {result.did_estimate:.4f}
-  = {result.standard_error:.4f}
- t = {result.t_statistic:.4f}
- p = {result.p_value:.4f}
- {'' if result.p_value < 0.05 else ''} (5%)

 
-  = {result.pre_treatment_diff:.4f}
-  = {result.post_treatment_diff:.4f}
- () = {result.time_trend:.4f}

 """
    
    for key, value in result.parallel_trend_test.items():
        result_text += f"\n- {key}: {value:.4f}"
    
    result_text += "\n\n DID"
    result_text += "\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )



# ============================================================================
#  ()
# ============================================================================

async def handle_scatter_plot(ctx, x_data, y_data, x_label="X", y_label="Y", 
                              title="", add_regression_line=True, **kwargs):
    """"""
    from .visualization import scatter_plot
    
    result = scatter_plot(x_data, y_data, x_label, y_label, title, add_regression_line)
    
    result_text = f""" 

 
-  = scatter
-  = {result.n_observations}
-  = {', '.join(result.variables)}
-  = {'' if add_regression_line else ''}

 
{result.description}

 Base64"""
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_histogram_plot(ctx, data, bins=30, label="", 
                                title="", show_density=True, **kwargs):
    """"""
    from .visualization import histogram
    
    result = histogram(data, bins, label, title, show_density)
    
    result_text = f""" 

 
-  = histogram
-  = {result.n_observations}
-  = {bins}
-  = {'' if show_density else ''}

 
{result.description}

 Base64"""
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_correlation_heatmap(ctx, data, title="", 
                                     method="pearson", **kwargs):
    """"""
    from .visualization import correlation_matrix_plot
    
    result = correlation_matrix_plot(data, title, method)
    
    result_text = f""" 

 
-  = correlation_matrix
-  = {len(result.variables)}
-  = {method}
-  = {result.n_observations}

 
{', '.join(result.variables)}

 
{result.description}

 """
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


# ============================================================================
#  ()
# ============================================================================

async def handle_wls_regression(ctx, y_data, x_data, weights=None, 
                                weight_type="manual", feature_names=None, **kwargs):
    """"""
    from .advanced_regression import weighted_least_squares
    
    result = weighted_least_squares(y_data, x_data, weights, weight_type, feature_names)
    
    result_text = f""" (WLS)

 
- R² = {result.r_squared:.4f}
- R² = {result.weighted_r_squared:.4f}
-  = {result.n_observations}
-  = {result.weight_type}

 """
    
    for var_name, coef_info in result.coefficients.items():
        sig = "***" if coef_info["p_value"] < 0.01 else "**" if coef_info["p_value"] < 0.05 else "*" if coef_info["p_value"] < 0.1 else ""
        result_text += f"\n- {var_name}: {coef_info['coefficient']:.4f}{sig} (se={coef_info['std_error']:.4f}, t={coef_info['t_statistic']:.4f}, p={coef_info['p_value']:.4f})"
    
    result_text += "\n\n WLS"
    result_text += "\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_gmm_estimation(ctx, y_data, x_data, instruments, 
                                feature_names=None, weight_matrix="optimal", **kwargs):
    """GMM"""
    from .advanced_regression import gmm_estimation
    
    result = gmm_estimation(y_data, x_data, instruments, feature_names, weight_matrix)
    
    result_text = f""" (GMM)

 
-  = {result.n_observations}
-  = {result.n_moments}
-  = {weight_matrix}

 
- J = {result.j_statistic:.4f}
- Jp = {result.j_pvalue:.4f}
- {'' if result.j_pvalue > 0.05 else ' '}

 GMM"""
    
    for var_name, coef_info in result.coefficients.items():
        sig = "***" if coef_info["p_value"] < 0.01 else "**" if coef_info["p_value"] < 0.05 else "*" if coef_info["p_value"] < 0.1 else ""
        result_text += f"\n- {var_name}: {coef_info['coefficient']:.4f}{sig} (se={coef_info['std_error']:.4f}, z={coef_info['z_statistic']:.4f}, p={coef_info['p_value']:.4f})"
    
    result_text += "\n\n GMM"
    result_text += "\n\n Jp>0.05"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_bootstrap_analysis(ctx, data, statistic_func="mean", 
                                    n_bootstrap=1000, confidence_level=0.95, **kwargs):
    """Bootstrap"""
    from .advanced_regression import bootstrap_inference
    
    result = bootstrap_inference(data, statistic_func, n_bootstrap, confidence_level)
    
    result_text = f""" Bootstrap

 
-  = {statistic_func}
- Bootstrap = {result.n_bootstrap}
-  = {confidence_level*100:.0f}%

 
-  = {result.original_estimate:.4f}
- Bootstrap = {result.bootstrap_mean:.4f}
- Bootstrap = {result.bootstrap_std:.4f}
-  = {result.bias:.4f}
- {confidence_level*100:.0f}% = [{result.confidence_interval[0]:.4f}, {result.confidence_interval[1]:.4f}]

 Bootstrap"""
    result_text += "\n\n Bootstrap(≥1000)"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )

async def handle_iv_regression(ctx, y_data, x_data, instruments, feature_names=None, instrument_names=None, **kwargs):
    """"""
    from .advanced_regression import instrumental_variables_regression
    
    result = instrumental_variables_regression(y_data, x_data, instruments, feature_names, instrument_names)
    
    result_text = f""" (IV/2SLS)

 
- R² = {result.r_squared:.4f}
-  = {result.n_observations}
-  = {result.n_instruments}

 
- F = {result.first_stage_f:.4f}
- {'' if result.first_stage_f > 10 else ' ' if result.first_stage_f > 5 else ' '}
- Sargan = {result.sargan_statistic:.4f}
- Sarganp = {result.sargan_pvalue:.4f}

 """
    
    for var_name, coef_info in result.coefficients.items():
        sig = "***" if coef_info["p_value"] < 0.01 else "**" if coef_info["p_value"] < 0.05 else "*" if coef_info["p_value"] < 0.1 else ""
        result_text += f"\n- {var_name}: {coef_info['coefficient']:.4f}{sig} (se={coef_info['std_error']:.4f}, t={coef_info['t_statistic']:.4f}, p={coef_info['p_value']:.4f})"
    
    result_text += "\n\n IV/2SLS"
    result_text += "\n\n (F>10)Sarganp>0.05"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


# ============================================================================
#  ()
# ============================================================================

async def handle_data_cleaning(ctx, data, handle_missing="drop", handle_outliers="keep", 
                               outlier_method="iqr", outlier_threshold=3.0, **kwargs):
    """"""
    from .data_management import clean_data
    
    result = clean_data(data, handle_missing, handle_outliers, outlier_method, outlier_threshold)
    
    result_text = f""" 

 
- : {result.original_size} × {len(result.variables)}
- : {result.cleaned_size} × {len(result.variables)}
- : {(result.original_size - result.cleaned_size) / result.original_size * 100:.1f}%

 
-  = {handle_missing}
-  = {result.n_missing_removed}
-  = {handle_outliers}
-  = {result.n_outliers_removed}

 """
    
    for var in result.variables:
        result_text += f"\n- {var}"
    
    result_text += "\n\n "
    result_text += "\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_data_merge(ctx, left_data, right_data, on, how="inner", **kwargs):
    """"""
    from .data_management import merge_data
    
    result = merge_data(left_data, right_data, on, how)
    
    result_text = f""" 

 
-  = {result.merge_type}
-  = {result.key_variable}
-  = {result.n_matched}

 
- () = {result.n_unmatched_left}
- () = {result.n_unmatched_right}
-  = {len(next(iter(result.merged_data.values())))}

 """
    
    for var in result.merged_data.keys():
        result_text += f"\n- {var}"
    
    result_text += f"\n\n "
    result_text += f"\n- inner: "
    result_text += f"\n- left: "
    result_text += f"\n- right: "
    result_text += f"\n- outer: "
    
    result_text += "\n\n "
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_reshape_to_long(ctx, data, id_vars, value_vars, var_name="variable", value_name="value", **kwargs):
    """"""
    from .data_management import reshape_wide_to_long
    
    result = reshape_wide_to_long(data, id_vars, value_vars, var_name, value_name)
    
    result_text = f""" →

 
- : {result.original_shape[0]} × {result.original_shape[1]}
- : {result.new_shape[0]} × {result.new_shape[1]}
- : {result.new_shape[0] / result.original_shape[0]:.1f}

 
- ID: {', '.join(result.id_vars)}
- : {', '.join(result.value_vars)}
-  = {var_name}
-  = {value_name}

 """
    
    for var in result.reshaped_data.keys():
        result_text += f"\n- {var}"
    
    result_text += "\n\n "
    result_text += "\n\n ID"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )


async def handle_reshape_to_wide(ctx, data, id_var, variable_col, value_col, **kwargs):
    """"""
    from .data_management import reshape_long_to_wide
    
    result = reshape_long_to_wide(data, id_var, variable_col, value_col)
    
    result_text = f""" →

 
- : {result.original_shape[0]} × {result.original_shape[1]}
- : {result.new_shape[0]} × {result.new_shape[1]}
- : {result.original_shape[0] / result.new_shape[0]:.1f}

 
- ID: {result.id_vars[0]}
- : {result.value_vars[0]}

 """
    
    for var in result.reshaped_data.keys():
        result_text += f"\n- {var}"
    
    result_text += "\n\n "
    result_text += "\n\n ID"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        structuredContent=result.model_dump()
    )
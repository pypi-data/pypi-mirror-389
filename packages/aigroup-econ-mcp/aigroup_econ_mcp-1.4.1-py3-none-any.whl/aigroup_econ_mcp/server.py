"""
AIGroup  MCP  - 
80%
"""

from typing import Dict, Any, Optional, List, Annotated
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from mcp.types import CallToolResult, TextContent

# 
from .tools.tool_handlers import (
    handle_descriptive_statistics,
    handle_ols_regression,
    handle_hypothesis_testing,
    handle_time_series_analysis,
    handle_correlation_analysis,
    handle_panel_fixed_effects,
    handle_panel_random_effects,
    handle_panel_hausman_test,
    handle_panel_unit_root_test,
    handle_var_model,
    handle_vecm_model,
    handle_garch_model,
    handle_state_space_model,
    handle_variance_decomposition,
    handle_random_forest,
    handle_gradient_boosting,
    handle_lasso_regression,
    handle_ridge_regression,
    handle_cross_validation,
    handle_feature_importance
)

# 
from .tools.base import with_file_support_decorator as econometric_tool
from .tools.tool_descriptions import (
    get_tool_description,
    get_field_description,
    DESCRIPTIVE_STATISTICS,
    OLS_REGRESSION,
    HYPOTHESIS_TESTING,
    TIME_SERIES_ANALYSIS,
    CORRELATION_ANALYSIS,
    PANEL_FIXED_EFFECTS,
    PANEL_RANDOM_EFFECTS,
    PANEL_HAUSMAN_TEST,
    PANEL_UNIT_ROOT_TEST,
    VAR_MODEL_ANALYSIS,
    VECM_MODEL_ANALYSIS,
    GARCH_MODEL_ANALYSIS,
    STATE_SPACE_MODEL_ANALYSIS,
    VARIANCE_DECOMPOSITION_ANALYSIS,
    RANDOM_FOREST_REGRESSION_ANALYSIS,
    GRADIENT_BOOSTING_REGRESSION_ANALYSIS,
    LASSO_REGRESSION_ANALYSIS,
    RIDGE_REGRESSION_ANALYSIS,
    CROSS_VALIDATION_ANALYSIS,
    FEATURE_IMPORTANCE_ANALYSIS_TOOL,
    # 
    LOGIT_REGRESSION,
    PROBIT_REGRESSION,
    POISSON_COUNT_REGRESSION,
    PROPENSITY_SCORE_MATCHING,
    DIFFERENCE_IN_DIFFERENCES,
    INSTRUMENTAL_VARIABLES_REGRESSION,
    DATA_CLEANING,
    DATA_MERGE,
    RESHAPE_TO_LONG,
    RESHAPE_TO_WIDE,
    # 
    SCATTER_PLOT,
    HISTOGRAM_PLOT,
    CORRELATION_HEATMAP,
    WLS_REGRESSION,
    GMM_ESTIMATION,
    BOOTSTRAP_ANALYSIS
)


# 
@dataclass
class AppContext:
    """"""
    config: Dict[str, Any]
    version: str = "1.0.0"


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """"""
    config = {
        "max_sample_size": 10000,
        "default_significance_level": 0.05,
        "supported_tests": ["t_test", "f_test", "chi_square", "adf"],
        "data_types": ["cross_section", "time_series", "panel"]
    }
    try:
        yield AppContext(config=config, version="1.0.0")
    finally:
        pass


# MCP
mcp = FastMCP(
    name="aigroup-econ-mcp",
    instructions="Econometrics MCP Server - Provides data analysis with automatic file input support",
    lifespan=lifespan
)


# ============================================================================
#  (5) - 
# ============================================================================

@mcp.tool()
@econometric_tool('multi_var_dict')
async def descriptive_statistics(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=DESCRIPTIVE_STATISTICS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=DESCRIPTIVE_STATISTICS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=DESCRIPTIVE_STATISTICS.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[Dict[str, List[float]]], Field(default=None, description=DESCRIPTIVE_STATISTICS.get_field_description("data"))] = None
) -> CallToolResult:
    """"""
    return await handle_descriptive_statistics(ctx, data=data)


@mcp.tool()
@econometric_tool('regression')
async def ols_regression(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=OLS_REGRESSION.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=OLS_REGRESSION.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=OLS_REGRESSION.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=OLS_REGRESSION.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=OLS_REGRESSION.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=OLS_REGRESSION.get_field_description("feature_names"))] = None
) -> CallToolResult:
    """OLS"""
    return await handle_ols_regression(ctx, y_data=y_data, x_data=x_data, feature_names=feature_names)


@mcp.tool()
@econometric_tool('single_var')
async def hypothesis_testing(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=HYPOTHESIS_TESTING.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=HYPOTHESIS_TESTING.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=HYPOTHESIS_TESTING.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[List[float]], Field(default=None, description=HYPOTHESIS_TESTING.get_field_description("data"))] = None,
    data2: Annotated[Optional[List[float]], Field(default=None, description=HYPOTHESIS_TESTING.get_field_description("data2"))] = None,
    test_type: Annotated[str, Field(default="t_test", description=HYPOTHESIS_TESTING.get_field_description("test_type"))] = "t_test"
) -> CallToolResult:
    """ - """
    return await handle_hypothesis_testing(ctx, data1=data, data2=data2, test_type=test_type)


@mcp.tool()
@econometric_tool('single_var')
async def time_series_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=TIME_SERIES_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=TIME_SERIES_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=TIME_SERIES_ANALYSIS.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[List[float]], Field(default=None, description=TIME_SERIES_ANALYSIS.get_field_description("data"))] = None
) -> CallToolResult:
    """ - """
    return await handle_time_series_analysis(ctx, data=data)


@mcp.tool()
@econometric_tool('multi_var_dict')
async def correlation_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=CORRELATION_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=CORRELATION_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=CORRELATION_ANALYSIS.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[Dict[str, List[float]]], Field(default=None, description=CORRELATION_ANALYSIS.get_field_description("data"))] = None,
    method: Annotated[str, Field(default="pearson", description=CORRELATION_ANALYSIS.get_field_description("method"))] = "pearson"
) -> CallToolResult:
    """ - """
    return await handle_correlation_analysis(ctx, data=data, method=method)


# ============================================================================
#  (4) - 
# ============================================================================

@mcp.tool()
@econometric_tool('panel')
async def panel_fixed_effects(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=PANEL_FIXED_EFFECTS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=PANEL_FIXED_EFFECTS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=PANEL_FIXED_EFFECTS.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=PANEL_FIXED_EFFECTS.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=PANEL_FIXED_EFFECTS.get_field_description("x_data"))] = None,
    entity_ids: Annotated[Optional[List[str]], Field(default=None, description=PANEL_FIXED_EFFECTS.get_field_description("entity_ids"))] = None,
    time_periods: Annotated[Optional[List[str]], Field(default=None, description=PANEL_FIXED_EFFECTS.get_field_description("time_periods"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=PANEL_FIXED_EFFECTS.get_field_description("feature_names"))] = None,
    entity_effects: Annotated[bool, Field(default=True, description=PANEL_FIXED_EFFECTS.get_field_description("entity_effects"))] = True,
    time_effects: Annotated[bool, Field(default=False, description=PANEL_FIXED_EFFECTS.get_field_description("time_effects"))] = False
) -> CallToolResult:
    """ - """
    return await handle_panel_fixed_effects(ctx, y_data, x_data, entity_ids, time_periods,
                                           feature_names, entity_effects, time_effects)


@mcp.tool()
@econometric_tool('panel')
async def panel_random_effects(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=PANEL_RANDOM_EFFECTS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=PANEL_RANDOM_EFFECTS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=PANEL_RANDOM_EFFECTS.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=PANEL_RANDOM_EFFECTS.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=PANEL_RANDOM_EFFECTS.get_field_description("x_data"))] = None,
    entity_ids: Annotated[Optional[List[str]], Field(default=None, description=PANEL_RANDOM_EFFECTS.get_field_description("entity_ids"))] = None,
    time_periods: Annotated[Optional[List[str]], Field(default=None, description=PANEL_RANDOM_EFFECTS.get_field_description("time_periods"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=PANEL_RANDOM_EFFECTS.get_field_description("feature_names"))] = None,
    entity_effects: Annotated[bool, Field(default=True, description=PANEL_RANDOM_EFFECTS.get_field_description("entity_effects"))] = True,
    time_effects: Annotated[bool, Field(default=False, description=PANEL_RANDOM_EFFECTS.get_field_description("time_effects"))] = False
) -> CallToolResult:
    """ - """
    return await handle_panel_random_effects(ctx, y_data, x_data, entity_ids, time_periods,
                                            feature_names, entity_effects, time_effects)


@mcp.tool()
@econometric_tool('panel')
async def panel_hausman_test(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=PANEL_HAUSMAN_TEST.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=PANEL_HAUSMAN_TEST.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=PANEL_HAUSMAN_TEST.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=PANEL_HAUSMAN_TEST.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=PANEL_HAUSMAN_TEST.get_field_description("x_data"))] = None,
    entity_ids: Annotated[Optional[List[str]], Field(default=None, description=PANEL_HAUSMAN_TEST.get_field_description("entity_ids"))] = None,
    time_periods: Annotated[Optional[List[str]], Field(default=None, description=PANEL_HAUSMAN_TEST.get_field_description("time_periods"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=PANEL_HAUSMAN_TEST.get_field_description("feature_names"))] = None
) -> CallToolResult:
    """Hausman - """
    return await handle_panel_hausman_test(ctx, y_data, x_data, entity_ids, time_periods, feature_names)


@mcp.tool()
@econometric_tool('panel')  # panelentity_idstime_periods
async def panel_unit_root_test(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=PANEL_UNIT_ROOT_TEST.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=PANEL_UNIT_ROOT_TEST.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=PANEL_UNIT_ROOT_TEST.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[List[float]], Field(default=None, description=PANEL_UNIT_ROOT_TEST.get_field_description("data"))] = None,
    y_data: Annotated[Optional[List[float]], Field(default=None, description=PANEL_UNIT_ROOT_TEST.get_field_description("y_data"))] = None,  # panel
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=PANEL_UNIT_ROOT_TEST.get_field_description("x_data"))] = None,  # panel
    entity_ids: Annotated[Optional[List[str]], Field(default=None, description=PANEL_UNIT_ROOT_TEST.get_field_description("entity_ids"))] = None,
    time_periods: Annotated[Optional[List[str]], Field(default=None, description=PANEL_UNIT_ROOT_TEST.get_field_description("time_periods"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=PANEL_UNIT_ROOT_TEST.get_field_description("feature_names"))] = None,  # panel
    test_type: Annotated[str, Field(default="levinlin", description=PANEL_UNIT_ROOT_TEST.get_field_description("test_type"))] = "levinlin"
) -> CallToolResult:
    """ - """
    # handler
    return await handle_panel_unit_root_test(
        ctx,
        data=data,
        y_data=y_data,
        entity_ids=entity_ids,
        time_periods=time_periods,
        test_type=test_type
    )


# ============================================================================
#  (5) - 
# ============================================================================

@mcp.tool()
@econometric_tool('time_series')
async def var_model_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=VAR_MODEL_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=VAR_MODEL_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=VAR_MODEL_ANALYSIS.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[Dict[str, List[float]]], Field(default=None, description=VAR_MODEL_ANALYSIS.get_field_description("data"))] = None,
    max_lags: Annotated[int, Field(default=5, description=VAR_MODEL_ANALYSIS.get_field_description("max_lags"))] = 5,
    ic: Annotated[str, Field(default="aic", description=VAR_MODEL_ANALYSIS.get_field_description("ic"))] = "aic"
) -> CallToolResult:
    """VAR - """
    return await handle_var_model(ctx, data, max_lags, ic)


@mcp.tool()
@econometric_tool('time_series')
async def vecm_model_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=VECM_MODEL_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=VECM_MODEL_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=VECM_MODEL_ANALYSIS.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[Dict[str, List[float]]], Field(default=None, description=VECM_MODEL_ANALYSIS.get_field_description("data"))] = None,
    coint_rank: Annotated[int, Field(default=1, description=VECM_MODEL_ANALYSIS.get_field_description("coint_rank"))] = 1,
    deterministic: Annotated[str, Field(default="co", description=VECM_MODEL_ANALYSIS.get_field_description("deterministic"))] = "co",
    max_lags: Annotated[int, Field(default=5, description=VECM_MODEL_ANALYSIS.get_field_description("max_lags"))] = 5
) -> CallToolResult:
    """VECM - """
    return await handle_vecm_model(ctx, data, coint_rank, deterministic, max_lags)


@mcp.tool()
@econometric_tool('single_var')
async def garch_model_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=GARCH_MODEL_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=GARCH_MODEL_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=GARCH_MODEL_ANALYSIS.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[List[float]], Field(default=None, description=GARCH_MODEL_ANALYSIS.get_field_description("data"))] = None,
    order: Annotated[tuple, Field(default=(1, 1), description=GARCH_MODEL_ANALYSIS.get_field_description("order"))] = (1, 1),
    dist: Annotated[str, Field(default="normal", description=GARCH_MODEL_ANALYSIS.get_field_description("dist"))] = "normal"
) -> CallToolResult:
    """GARCH - """
    return await handle_garch_model(ctx, data, order, dist)


@mcp.tool()
@econometric_tool('single_var')
async def state_space_model_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[List[float]], Field(default=None, description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("data"))] = None,
    state_dim: Annotated[int, Field(default=1, description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("state_dim"))] = 1,
    observation_dim: Annotated[int, Field(default=1, description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("observation_dim"))] = 1,
    trend: Annotated[bool, Field(default=True, description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("trend"))] = True,
    seasonal: Annotated[bool, Field(default=False, description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("seasonal"))] = False,
    period: Annotated[int, Field(default=12, description=STATE_SPACE_MODEL_ANALYSIS.get_field_description("period"))] = 12
) -> CallToolResult:
    """ - """
    return await handle_state_space_model(ctx, data, state_dim, observation_dim, trend, seasonal, period)


@mcp.tool()
@econometric_tool('time_series')
async def variance_decomposition_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=VARIANCE_DECOMPOSITION_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=VARIANCE_DECOMPOSITION_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=VARIANCE_DECOMPOSITION_ANALYSIS.get_field_description("file_format"))] = "auto",
    data: Annotated[Optional[Dict[str, List[float]]], Field(default=None, description=VARIANCE_DECOMPOSITION_ANALYSIS.get_field_description("data"))] = None,
    periods: Annotated[int, Field(default=10, description=VARIANCE_DECOMPOSITION_ANALYSIS.get_field_description("periods"))] = 10,
    max_lags: Annotated[int, Field(default=5, description=VARIANCE_DECOMPOSITION_ANALYSIS.get_field_description("max_lags"))] = 5
) -> CallToolResult:
    """ - """
    return await handle_variance_decomposition(ctx, data, periods, max_lags)


# ============================================================================
#  (6) - 
# ============================================================================

@mcp.tool()
@econometric_tool('regression')
async def random_forest_regression_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=RANDOM_FOREST_REGRESSION_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=RANDOM_FOREST_REGRESSION_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=RANDOM_FOREST_REGRESSION_ANALYSIS.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=RANDOM_FOREST_REGRESSION_ANALYSIS.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=RANDOM_FOREST_REGRESSION_ANALYSIS.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=RANDOM_FOREST_REGRESSION_ANALYSIS.get_field_description("feature_names"))] = None,
    n_estimators: Annotated[int, Field(default=100, description=RANDOM_FOREST_REGRESSION_ANALYSIS.get_field_description("n_estimators"))] = 100,
    max_depth: Annotated[Optional[int], Field(default=None, description=RANDOM_FOREST_REGRESSION_ANALYSIS.get_field_description("max_depth"))] = None
) -> CallToolResult:
    """ - """
    return await handle_random_forest(ctx, y_data, x_data, feature_names, n_estimators, max_depth)


@mcp.tool()
@econometric_tool('regression')
async def gradient_boosting_regression_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("feature_names"))] = None,
    n_estimators: Annotated[int, Field(default=100, description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("n_estimators"))] = 100,
    learning_rate: Annotated[float, Field(default=0.1, description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("learning_rate"))] = 0.1,
    max_depth: Annotated[int, Field(default=3, description=GRADIENT_BOOSTING_REGRESSION_ANALYSIS.get_field_description("max_depth"))] = 3
) -> CallToolResult:
    """ - """
    return await handle_gradient_boosting(ctx, y_data, x_data, feature_names, n_estimators, learning_rate, max_depth)


@mcp.tool()
@econometric_tool('regression')
async def lasso_regression_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=LASSO_REGRESSION_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=LASSO_REGRESSION_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=LASSO_REGRESSION_ANALYSIS.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=LASSO_REGRESSION_ANALYSIS.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=LASSO_REGRESSION_ANALYSIS.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=LASSO_REGRESSION_ANALYSIS.get_field_description("feature_names"))] = None,
    alpha: Annotated[float, Field(default=1.0, description=LASSO_REGRESSION_ANALYSIS.get_field_description("alpha"))] = 1.0
) -> CallToolResult:
    """Lasso - """
    return await handle_lasso_regression(ctx, y_data, x_data, feature_names, alpha)


@mcp.tool()
@econometric_tool('regression')
async def ridge_regression_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=RIDGE_REGRESSION_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=RIDGE_REGRESSION_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=RIDGE_REGRESSION_ANALYSIS.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=RIDGE_REGRESSION_ANALYSIS.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=RIDGE_REGRESSION_ANALYSIS.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=RIDGE_REGRESSION_ANALYSIS.get_field_description("feature_names"))] = None,
    alpha: Annotated[float, Field(default=1.0, description=RIDGE_REGRESSION_ANALYSIS.get_field_description("alpha"))] = 1.0
) -> CallToolResult:
    """Ridge - """
    return await handle_ridge_regression(ctx, y_data, x_data, feature_names, alpha)


@mcp.tool()
@econometric_tool('regression')
async def cross_validation_analysis(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=CROSS_VALIDATION_ANALYSIS.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=CROSS_VALIDATION_ANALYSIS.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=CROSS_VALIDATION_ANALYSIS.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=CROSS_VALIDATION_ANALYSIS.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=CROSS_VALIDATION_ANALYSIS.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=CROSS_VALIDATION_ANALYSIS.get_field_description("feature_names"))] = None,
    model_type: Annotated[str, Field(default="random_forest", description=CROSS_VALIDATION_ANALYSIS.get_field_description("model_type"))] = "random_forest",
    cv_folds: Annotated[int, Field(default=5, description=CROSS_VALIDATION_ANALYSIS.get_field_description("cv_folds"))] = 5,
    scoring: Annotated[str, Field(default="r2", description=CROSS_VALIDATION_ANALYSIS.get_field_description("scoring"))] = "r2"
) -> CallToolResult:
    """ - """
    return await handle_cross_validation(ctx, y_data, x_data, model_type, cv_folds, scoring)


@mcp.tool()
@econometric_tool('regression')
async def feature_importance_analysis_tool(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None, description=FEATURE_IMPORTANCE_ANALYSIS_TOOL.get_field_description("file_path"))] = None,
    file_content: Annotated[Optional[str], Field(default=None, description=FEATURE_IMPORTANCE_ANALYSIS_TOOL.get_field_description("file_content"))] = None,
    file_format: Annotated[str, Field(default="auto", description=FEATURE_IMPORTANCE_ANALYSIS_TOOL.get_field_description("file_format"))] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=FEATURE_IMPORTANCE_ANALYSIS_TOOL.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=FEATURE_IMPORTANCE_ANALYSIS_TOOL.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=FEATURE_IMPORTANCE_ANALYSIS_TOOL.get_field_description("feature_names"))] = None,
    method: Annotated[str, Field(default="random_forest", description=FEATURE_IMPORTANCE_ANALYSIS_TOOL.get_field_description("method"))] = "random_forest",
    top_k: Annotated[int, Field(default=5, description=FEATURE_IMPORTANCE_ANALYSIS_TOOL.get_field_description("top_k"))] = 5
) -> CallToolResult:
    """ - """
    return await handle_feature_importance(ctx, y_data, x_data, feature_names, method, top_k)


# ============================================================================
#  () - 
# ============================================================================

@mcp.tool()
@econometric_tool('regression')
async def logit_regression(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None)] = None,
    file_content: Annotated[Optional[str], Field(default=None)] = None,
    file_format: Annotated[str, Field(default="auto")] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=LOGIT_REGRESSION.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=LOGIT_REGRESSION.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=LOGIT_REGRESSION.get_field_description("feature_names"))] = None
) -> CallToolResult:
    """Logit - """
    return await handle_logit_regression(ctx, y_data, x_data, feature_names)


@mcp.tool()
@econometric_tool('regression')
async def probit_regression(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None)] = None,
    file_content: Annotated[Optional[str], Field(default=None)] = None,
    file_format: Annotated[str, Field(default="auto")] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=PROBIT_REGRESSION.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=PROBIT_REGRESSION.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=PROBIT_REGRESSION.get_field_description("feature_names"))] = None
) -> CallToolResult:
    """Probit - """
    return await handle_probit_regression(ctx, y_data, x_data, feature_names)


@mcp.tool()
@econometric_tool('regression')
async def poisson_count_regression(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None)] = None,
    file_content: Annotated[Optional[str], Field(default=None)] = None,
    file_format: Annotated[str, Field(default="auto")] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=POISSON_COUNT_REGRESSION.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=POISSON_COUNT_REGRESSION.get_field_description("x_data"))] = None,
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=POISSON_COUNT_REGRESSION.get_field_description("feature_names"))] = None
) -> CallToolResult:
    """ - """
    return await handle_poisson_regression(ctx, y_data, x_data, feature_names)


# ============================================================================
#  ()
# ============================================================================

@mcp.tool()
async def propensity_score_matching(
    ctx: Context[ServerSession, AppContext],
    treatment: Annotated[List[int], Field(description=PROPENSITY_SCORE_MATCHING.get_field_description("treatment"))],
    covariates: Annotated[List[List[float]], Field(description=PROPENSITY_SCORE_MATCHING.get_field_description("covariates"))],
    outcome: Annotated[List[float], Field(description=PROPENSITY_SCORE_MATCHING.get_field_description("outcome"))],
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=PROPENSITY_SCORE_MATCHING.get_field_description("feature_names"))] = None,
    caliper: Annotated[float, Field(default=0.2, description=PROPENSITY_SCORE_MATCHING.get_field_description("caliper"))] = 0.2
) -> CallToolResult:
    """(PSM) - """
    return await handle_psm(ctx, treatment, covariates, outcome, feature_names, caliper)


@mcp.tool()
async def difference_in_differences(
    ctx: Context[ServerSession, AppContext],
    treatment: Annotated[List[int], Field(description=DIFFERENCE_IN_DIFFERENCES.get_field_description("treatment"))],
    time_period: Annotated[List[int], Field(description=DIFFERENCE_IN_DIFFERENCES.get_field_description("time_period"))],
    outcome: Annotated[List[float], Field(description=DIFFERENCE_IN_DIFFERENCES.get_field_description("outcome"))],
    covariates: Annotated[Optional[List[List[float]]], Field(default=None, description=DIFFERENCE_IN_DIFFERENCES.get_field_description("covariates"))] = None
) -> CallToolResult:
    """(DID) - """
    return await handle_did(ctx, treatment, time_period, outcome, covariates)


@mcp.tool()
async def instrumental_variables_regression(
    ctx: Context[ServerSession, AppContext],
    y_data: Annotated[List[float], Field(description=INSTRUMENTAL_VARIABLES_REGRESSION.get_field_description("y_data"))],
    x_data: Annotated[List[List[float]], Field(description=INSTRUMENTAL_VARIABLES_REGRESSION.get_field_description("x_data"))],
    instruments: Annotated[List[List[float]], Field(description=INSTRUMENTAL_VARIABLES_REGRESSION.get_field_description("instruments"))],
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=INSTRUMENTAL_VARIABLES_REGRESSION.get_field_description("feature_names"))] = None,
    instrument_names: Annotated[Optional[List[str]], Field(default=None, description=INSTRUMENTAL_VARIABLES_REGRESSION.get_field_description("instrument_names"))] = None
) -> CallToolResult:
    """/2SLS - """
    return await handle_iv_regression(ctx, y_data, x_data, instruments, feature_names, instrument_names)


# ============================================================================
#  () - 
# ============================================================================

@mcp.tool()
@econometric_tool('multi_var_dict')
async def data_cleaning(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None)] = None,
    file_content: Annotated[Optional[str], Field(default=None)] = None,
    file_format: Annotated[str, Field(default="auto")] = "auto",
    data: Annotated[Optional[Dict[str, List[float]]], Field(default=None, description=DATA_CLEANING.get_field_description("data"))] = None,
    handle_missing: Annotated[str, Field(default="drop", description=DATA_CLEANING.get_field_description("handle_missing"))] = "drop",
    handle_outliers: Annotated[str, Field(default="keep", description=DATA_CLEANING.get_field_description("handle_outliers"))] = "keep",
    outlier_method: Annotated[str, Field(default="iqr", description=DATA_CLEANING.get_field_description("outlier_method"))] = "iqr",
    outlier_threshold: Annotated[float, Field(default=3.0, description=DATA_CLEANING.get_field_description("outlier_threshold"))] = 3.0
) -> CallToolResult:
    """ - """
    return await handle_data_cleaning(ctx, data, handle_missing, handle_outliers, outlier_method, outlier_threshold)


@mcp.tool()
async def data_merge(
    ctx: Context[ServerSession, AppContext],
    left_data: Annotated[Dict[str, List], Field(description=DATA_MERGE.get_field_description("left_data"))],
    right_data: Annotated[Dict[str, List], Field(description=DATA_MERGE.get_field_description("right_data"))],
    on: Annotated[str, Field(description=DATA_MERGE.get_field_description("on"))],
    how: Annotated[str, Field(default="inner", description=DATA_MERGE.get_field_description("how"))] = "inner"
) -> CallToolResult:
    """ - Statamerge"""
    return await handle_data_merge(ctx, left_data, right_data, on, how)


@mcp.tool()
@econometric_tool('multi_var_dict')
async def reshape_to_long(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None)] = None,
    file_content: Annotated[Optional[str], Field(default=None)] = None,
    file_format: Annotated[str, Field(default="auto")] = "auto",
    data: Annotated[Optional[Dict[str, List]], Field(default=None, description=RESHAPE_TO_LONG.get_field_description("data"))] = None,
    id_vars: Annotated[List[str], Field(description=RESHAPE_TO_LONG.get_field_description("id_vars"))] = None,
    value_vars: Annotated[List[str], Field(description=RESHAPE_TO_LONG.get_field_description("value_vars"))] = None,
    var_name: Annotated[str, Field(default="variable", description=RESHAPE_TO_LONG.get_field_description("var_name"))] = "variable",
    value_name: Annotated[str, Field(default="value", description=RESHAPE_TO_LONG.get_field_description("value_name"))] = "value"
) -> CallToolResult:
    """→"""
    return await handle_reshape_to_long(ctx, data, id_vars, value_vars, var_name, value_name)


@mcp.tool()
@econometric_tool('multi_var_dict')
async def reshape_to_wide(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None)] = None,
    file_content: Annotated[Optional[str], Field(default=None)] = None,
    file_format: Annotated[str, Field(default="auto")] = "auto",
    data: Annotated[Optional[Dict[str, List]], Field(default=None, description=RESHAPE_TO_WIDE.get_field_description("data"))] = None,
    id_var: Annotated[str, Field(description=RESHAPE_TO_WIDE.get_field_description("id_var"))] = None,
    variable_col: Annotated[str, Field(description=RESHAPE_TO_WIDE.get_field_description("variable_col"))] = None,
    value_col: Annotated[str, Field(description=RESHAPE_TO_WIDE.get_field_description("value_col"))] = None
) -> CallToolResult:
    """→"""
    return await handle_reshape_to_wide(ctx, data, id_var, variable_col, value_col)


# ============================================================================
#  ()
# ============================================================================

@mcp.tool()
async def scatter_plot(
    ctx: Context[ServerSession, AppContext],
    x_data: Annotated[List[float], Field(description=SCATTER_PLOT.get_field_description("x_data"))],
    y_data: Annotated[List[float], Field(description=SCATTER_PLOT.get_field_description("y_data"))],
    x_label: Annotated[str, Field(default="X", description=SCATTER_PLOT.get_field_description("x_label"))] = "X",
    y_label: Annotated[str, Field(default="Y", description=SCATTER_PLOT.get_field_description("y_label"))] = "Y",
    title: Annotated[str, Field(default="", description=SCATTER_PLOT.get_field_description("title"))] = "",
    add_regression_line: Annotated[bool, Field(default=True, description=SCATTER_PLOT.get_field_description("add_regression_line"))] = True
) -> CallToolResult:
    """ - """
    return await handle_scatter_plot(ctx, x_data, y_data, x_label, y_label, title, add_regression_line)


@mcp.tool()
async def histogram_plot(
    ctx: Context[ServerSession, AppContext],
    data: Annotated[List[float], Field(description=HISTOGRAM_PLOT.get_field_description("data"))],
    bins: Annotated[int, Field(default=30, description=HISTOGRAM_PLOT.get_field_description("bins"))] = 30,
    label: Annotated[str, Field(default="", description=HISTOGRAM_PLOT.get_field_description("label"))] = "",
    title: Annotated[str, Field(default="", description=HISTOGRAM_PLOT.get_field_description("title"))] = "",
    show_density: Annotated[bool, Field(default=True, description=HISTOGRAM_PLOT.get_field_description("show_density"))] = True
) -> CallToolResult:
    """ - """
    return await handle_histogram_plot(ctx, data, bins, label, title, show_density)


@mcp.tool()
@econometric_tool('multi_var_dict')
async def correlation_heatmap(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None)] = None,
    file_content: Annotated[Optional[str], Field(default=None)] = None,
    file_format: Annotated[str, Field(default="auto")] = "auto",
    data: Annotated[Optional[Dict[str, List[float]]], Field(default=None, description=CORRELATION_HEATMAP.get_field_description("data"))] = None,
    title: Annotated[str, Field(default="", description=CORRELATION_HEATMAP.get_field_description("title"))] = "",
    method: Annotated[str, Field(default="pearson", description=CORRELATION_HEATMAP.get_field_description("method"))] = "pearson"
) -> CallToolResult:
    """"""
    return await handle_correlation_heatmap(ctx, data, title, method)


# ============================================================================
#  ()
# ============================================================================

@mcp.tool()
@econometric_tool('regression')
async def wls_regression(
    ctx: Context[ServerSession, AppContext],
    file_path: Annotated[Optional[str], Field(default=None)] = None,
    file_content: Annotated[Optional[str], Field(default=None)] = None,
    file_format: Annotated[str, Field(default="auto")] = "auto",
    y_data: Annotated[Optional[List[float]], Field(default=None, description=WLS_REGRESSION.get_field_description("y_data"))] = None,
    x_data: Annotated[Optional[List[List[float]]], Field(default=None, description=WLS_REGRESSION.get_field_description("x_data"))] = None,
    weights: Annotated[Optional[List[float]], Field(default=None, description=WLS_REGRESSION.get_field_description("weights"))] = None,
    weight_type: Annotated[str, Field(default="manual", description=WLS_REGRESSION.get_field_description("weight_type"))] = "manual",
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=WLS_REGRESSION.get_field_description("feature_names"))] = None
) -> CallToolResult:
    """(WLS) - """
    return await handle_wls_regression(ctx, y_data, x_data, weights, weight_type, feature_names)


@mcp.tool()
async def gmm_estimation(
    ctx: Context[ServerSession, AppContext],
    y_data: Annotated[List[float], Field(description=GMM_ESTIMATION.get_field_description("y_data"))],
    x_data: Annotated[List[List[float]], Field(description=GMM_ESTIMATION.get_field_description("x_data"))],
    instruments: Annotated[List[List[float]], Field(description=GMM_ESTIMATION.get_field_description("instruments"))],
    feature_names: Annotated[Optional[List[str]], Field(default=None, description=GMM_ESTIMATION.get_field_description("feature_names"))] = None,
    weight_matrix: Annotated[str, Field(default="optimal", description=GMM_ESTIMATION.get_field_description("weight_matrix"))] = "optimal"
) -> CallToolResult:
    """(GMM)"""
    return await handle_gmm_estimation(ctx, y_data, x_data, instruments, feature_names, weight_matrix)


@mcp.tool()
async def bootstrap_analysis(
    ctx: Context[ServerSession, AppContext],
    data: Annotated[List[float], Field(description=BOOTSTRAP_ANALYSIS.get_field_description("data"))],
    statistic_func: Annotated[str, Field(default="mean", description=BOOTSTRAP_ANALYSIS.get_field_description("statistic_func"))] = "mean",
    n_bootstrap: Annotated[int, Field(default=1000, description=BOOTSTRAP_ANALYSIS.get_field_description("n_bootstrap"))] = 1000,
    confidence_level: Annotated[float, Field(default=0.95, description=BOOTSTRAP_ANALYSIS.get_field_description("confidence_level"))] = 0.95
) -> CallToolResult:
    """Bootstrap"""
    return await handle_bootstrap_analysis(ctx, data, statistic_func, n_bootstrap, confidence_level)


def create_mcp_server() -> FastMCP:
    """MCP"""
    return mcp
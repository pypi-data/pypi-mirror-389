"""
 - 
MCP

"""

from typing import Dict, Any, List, Optional
from pydantic import Field


class ToolDescription:
    """ - """
    
    def __init__(self, name: str, description: str, field_descriptions: Dict[str, str] = None,
                 examples: Optional[List[str]] = None, use_cases: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.field_descriptions = field_descriptions or {}
        self.examples = examples or []
        self.use_cases = use_cases or []
    
    def get_field_description(self, field_name: str, default: str = "") -> str:
        """"""
        return self.field_descriptions.get(field_name, default)
    
    def get_full_description(self) -> str:
        """"""
        full_desc = self.description
        if self.examples:
            full_desc += "\n\n:\n" + "\n".join(f"- {example}" for example in self.examples)
        if self.use_cases:
            full_desc += "\n\n:\n" + "\n".join(f"- {use_case}" for use_case in self.use_cases)
        return full_desc


# ============================================================================
#  (5)
# ============================================================================

DESCRIPTIVE_STATISTICS = ToolDescription(
    name="descriptive_statistics",
    description="""

file_path()file_content()data()
CSVJSONTXT//""",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "data": ""
    }
)

OLS_REGRESSION = ToolDescription(
    name="ols_regression",
    description="""OLS
    

CSV: """,
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "",
        "y_data": "()",
        "x_data": "()",
        "feature_names": ""
    }
)

HYPOTHESIS_TESTING = ToolDescription(
    name="hypothesis_testing",
    description=" - ",
    field_descriptions={
        "file_path": "",
        "file_content": "",
        "file_format": "",
        "data": "",
        "data2": "",
        "test_type": "(t_test/adf)"
    }
)

TIME_SERIES_ANALYSIS = ToolDescription(
    name="time_series_analysis",
    description=" - ",
    field_descriptions={
        "file_path": "",
        "file_content": "",
        "file_format": "",
        "data": ""
    }
)

CORRELATION_ANALYSIS = ToolDescription(
    name="correlation_analysis",
    description=" - ",
    field_descriptions={
        "file_path": "",
        "file_content": "",
        "file_format": "",
        "data": "",
        "method": ""
    }
)


# ============================================================================
#  (4)
# ============================================================================

PANEL_FIXED_EFFECTS = ToolDescription(
    name="panel_fixed_effects",
    description=" - ",
    field_descriptions={
        "file_path": "CSVCSVID(entity_id/id/entity/firm/company/country/region)(time_period/time/date/year/month/period/quarter)",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)CSV",
        "y_data": "",
        "x_data": "",
        "entity_ids": "ID ['A', 'B', 'C', ...]",
        "time_periods": " ['2020', '2021', '2022', ...]",
        "feature_names": " ['Investment', 'Employment', 'R&D']",
        "entity_effects": "True",
        "time_effects": "False"
    }
)

PANEL_RANDOM_EFFECTS = ToolDescription(
    name="panel_random_effects",
    description=" - ",
    field_descriptions={
        "file_path": "CSVCSVID",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "y_data": "",
        "x_data": "",
        "entity_ids": "ID",
        "time_periods": "",
        "feature_names": "",
        "entity_effects": "True",
        "time_effects": "False"
    }
)

PANEL_HAUSMAN_TEST = ToolDescription(
    name="panel_hausman_test",
    description="Hausman - ",
    field_descriptions={
        "file_path": "CSVCSVID",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "y_data": "",
        "x_data": "",
        "entity_ids": "ID",
        "time_periods": "",
        "feature_names": ""
    }
)

PANEL_UNIT_ROOT_TEST = ToolDescription(
    name="panel_unit_root_test",
    description=" - ",
    field_descriptions={
        "file_path": "CSVCSVID35",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "data": "",
        "y_data": "",
        "x_data": "",
        "entity_ids": "ID",
        "time_periods": "",
        "feature_names": "",
        "test_type": "(levinlin/ips/adf)"
    }
)


# ============================================================================
#  (5)
# ============================================================================

VAR_MODEL_ANALYSIS = ToolDescription(
    name="var_model_analysis",
    description="VAR - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "data": "",
        "max_lags": "5",
        "ic": "(aic/bic/hqic)aic"
    }
)

VECM_MODEL_ANALYSIS = ToolDescription(
    name="vecm_model_analysis",
    description="VECM - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "data": "",
        "coint_rank": "1",
        "deterministic": "(co/ci/lo/li)co",
        "max_lags": "5"
    }
)

GARCH_MODEL_ANALYSIS = ToolDescription(
    name="garch_model_analysis",
    description="GARCH - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "data": "",
        "order": "GARCH(p,q)(1,1)",
        "dist": "(normal/t/skewt)normal"
    }
)

STATE_SPACE_MODEL_ANALYSIS = ToolDescription(
    name="state_space_model_analysis",
    description=" - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "data": "",
        "state_dim": "1",
        "observation_dim": "1",
        "trend": "True",
        "seasonal": "False",
        "period": "12"
    }
)

VARIANCE_DECOMPOSITION_ANALYSIS = ToolDescription(
    name="variance_decomposition_analysis",
    description=" - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "data": "",
        "periods": "10",
        "max_lags": "5"
    }
)


# ============================================================================
#  (6)
# ============================================================================

RANDOM_FOREST_REGRESSION_ANALYSIS = ToolDescription(
    name="random_forest_regression_analysis",
    description=" - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "y_data": "",
        "x_data": "",
        "feature_names": "",
        "n_estimators": "100",
        "max_depth": "None"
    }
)

GRADIENT_BOOSTING_REGRESSION_ANALYSIS = ToolDescription(
    name="gradient_boosting_regression_analysis",
    description=" - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "y_data": "",
        "x_data": "",
        "feature_names": "",
        "n_estimators": "100",
        "learning_rate": "0.1",
        "max_depth": "3"
    }
)

LASSO_REGRESSION_ANALYSIS = ToolDescription(
    name="lasso_regression_analysis",
    description="Lasso - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "y_data": "",
        "x_data": "",
        "feature_names": "",
        "alpha": "1.0"
    }
)

RIDGE_REGRESSION_ANALYSIS = ToolDescription(
    name="ridge_regression_analysis",
    description="Ridge - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "y_data": "",
        "x_data": "",
        "feature_names": "",
        "alpha": "1.0"
    }
)

CROSS_VALIDATION_ANALYSIS = ToolDescription(
    name="cross_validation_analysis",
    description=" - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "y_data": "",
        "x_data": "",
        "feature_names": "",
        "model_type": "(random_forest/gradient_boosting/lasso/ridge)random_forest",
        "cv_folds": "5",
        "scoring": "(r2/mse/mae)r2"
    }
)

FEATURE_IMPORTANCE_ANALYSIS_TOOL = ToolDescription(
    name="feature_importance_analysis_tool",
    description=" - ",
    field_descriptions={
        "file_path": "CSV/JSON/TXT",
        "file_content": "CSV/JSON/TXT",
        "file_format": "(csv/json/txt/auto)",
        "y_data": "",
        "x_data": "",
        "feature_names": "",
        "method": "(random_forest/gradient_boosting/permutation)random_forest",
        "top_k": "K5"
    }
)


# ============================================================================
# 
# ============================================================================

def get_tool_description(tool_name: str) -> str:
    """"""
    tool_map = {
        "descriptive_statistics": DESCRIPTIVE_STATISTICS,
        "ols_regression": OLS_REGRESSION,
        "hypothesis_testing": HYPOTHESIS_TESTING,
        "time_series_analysis": TIME_SERIES_ANALYSIS,
        "correlation_analysis": CORRELATION_ANALYSIS,
        "panel_fixed_effects": PANEL_FIXED_EFFECTS,
        "panel_random_effects": PANEL_RANDOM_EFFECTS,
        "panel_hausman_test": PANEL_HAUSMAN_TEST,
        "panel_unit_root_test": PANEL_UNIT_ROOT_TEST,
        "var_model_analysis": VAR_MODEL_ANALYSIS,
        "vecm_model_analysis": VECM_MODEL_ANALYSIS,
        "garch_model_analysis": GARCH_MODEL_ANALYSIS,
        "state_space_model_analysis": STATE_SPACE_MODEL_ANALYSIS,
        "variance_decomposition_analysis": VARIANCE_DECOMPOSITION_ANALYSIS,
        "random_forest_regression_analysis": RANDOM_FOREST_REGRESSION_ANALYSIS,
        "gradient_boosting_regression_analysis": GRADIENT_BOOSTING_REGRESSION_ANALYSIS,
        "lasso_regression_analysis": LASSO_REGRESSION_ANALYSIS,
        "ridge_regression_analysis": RIDGE_REGRESSION_ANALYSIS,
        "cross_validation_analysis": CROSS_VALIDATION_ANALYSIS,
        "feature_importance_analysis_tool": FEATURE_IMPORTANCE_ANALYSIS_TOOL,
        # 
        "logit_regression": LOGIT_REGRESSION,
        "probit_regression": PROBIT_REGRESSION,
        "poisson_count_regression": POISSON_COUNT_REGRESSION,
        "propensity_score_matching": PROPENSITY_SCORE_MATCHING,
        "difference_in_differences": DIFFERENCE_IN_DIFFERENCES,
        "instrumental_variables_regression": INSTRUMENTAL_VARIABLES_REGRESSION,
        "data_cleaning": DATA_CLEANING,
        "data_merge": DATA_MERGE,
        "reshape_to_long": RESHAPE_TO_LONG,
        "reshape_to_wide": RESHAPE_TO_WIDE,
        # 
        "scatter_plot": SCATTER_PLOT,
        "histogram_plot": HISTOGRAM_PLOT,
        "correlation_heatmap": CORRELATION_HEATMAP,
        "wls_regression": WLS_REGRESSION,
        "gmm_estimation": GMM_ESTIMATION,
        "bootstrap_analysis": BOOTSTRAP_ANALYSIS
    }
    
    tool = tool_map.get(tool_name)
    if tool:
        return tool.get_full_description()
    return ""


def get_field_description(tool_name: str, field_name: str, default: str = "") -> str:
    """"""
    tool_map = {
        "descriptive_statistics": DESCRIPTIVE_STATISTICS,
        "ols_regression": OLS_REGRESSION,
        "hypothesis_testing": HYPOTHESIS_TESTING,
        "time_series_analysis": TIME_SERIES_ANALYSIS,
        "correlation_analysis": CORRELATION_ANALYSIS,
        "panel_fixed_effects": PANEL_FIXED_EFFECTS,
        "panel_random_effects": PANEL_RANDOM_EFFECTS,
        "panel_hausman_test": PANEL_HAUSMAN_TEST,
        "panel_unit_root_test": PANEL_UNIT_ROOT_TEST,
        "var_model_analysis": VAR_MODEL_ANALYSIS,
        "vecm_model_analysis": VECM_MODEL_ANALYSIS,
        "garch_model_analysis": GARCH_MODEL_ANALYSIS,
        "state_space_model_analysis": STATE_SPACE_MODEL_ANALYSIS,
        "variance_decomposition_analysis": VARIANCE_DECOMPOSITION_ANALYSIS,
        "random_forest_regression_analysis": RANDOM_FOREST_REGRESSION_ANALYSIS,
        "gradient_boosting_regression_analysis": GRADIENT_BOOSTING_REGRESSION_ANALYSIS,
        "lasso_regression_analysis": LASSO_REGRESSION_ANALYSIS,
        "ridge_regression_analysis": RIDGE_REGRESSION_ANALYSIS,
        "cross_validation_analysis": CROSS_VALIDATION_ANALYSIS,
        "feature_importance_analysis_tool": FEATURE_IMPORTANCE_ANALYSIS_TOOL,
        # 
        "logit_regression": LOGIT_REGRESSION,
        "probit_regression": PROBIT_REGRESSION,
        "poisson_count_regression": POISSON_COUNT_REGRESSION,
        "propensity_score_matching": PROPENSITY_SCORE_MATCHING,
        "difference_in_differences": DIFFERENCE_IN_DIFFERENCES,
        "instrumental_variables_regression": INSTRUMENTAL_VARIABLES_REGRESSION,
        "data_cleaning": DATA_CLEANING,
        "data_merge": DATA_MERGE,
        "reshape_to_long": RESHAPE_TO_LONG,
        "reshape_to_wide": RESHAPE_TO_WIDE
    }
    
    tool = tool_map.get(tool_name)
    if tool:
        return tool.get_field_description(field_name, default)
    return default

# ============================================================================
#  ( - 3)
# ============================================================================

LOGIT_REGRESSION = ToolDescription(
    name="logit_regression",
    description="Logit - ",
    field_descriptions={
        "y_data": "0/1",
        "x_data": "",
        "feature_names": ""
    },
    examples=[
        "/",
        "/",
        "/"
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)

PROBIT_REGRESSION = ToolDescription(
    name="probit_regression",
    description="Probit - ",
    field_descriptions={
        "y_data": "0/1",
        "x_data": "",
        "feature_names": ""
    },
    examples=[
        "",
        "",
        ""
    ],
    use_cases=[
        "Logit",
        "Probit",
        "Logit"
    ]
)

POISSON_COUNT_REGRESSION = ToolDescription(
    name="poisson_count_regression",
    description=" - ",
    field_descriptions={
        "y_data": "",
        "x_data": "",
        "feature_names": ""
    },
    examples=[
        "",
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)


# ============================================================================
#  ( - 3)
# ============================================================================

PROPENSITY_SCORE_MATCHING = ToolDescription(
    name="propensity_score_matching",
    description="(PSM) - ",
    field_descriptions={
        "treatment": "0=1=",
        "covariates": "",
        "outcome": "",
        "feature_names": "",
        "caliper": ""
    },
    examples=[
        "",
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)

DIFFERENCE_IN_DIFFERENCES = ToolDescription(
    name="difference_in_differences",
    description="(DID) - ",
    field_descriptions={
        "treatment": "0=1=",
        "time_period": "0=1=",
        "outcome": "",
        "covariates": ""
    },
    examples=[
        "",
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)

INSTRUMENTAL_VARIABLES_REGRESSION = ToolDescription(
    name="instrumental_variables_regression",
    description="/2SLS - ",
    field_descriptions={
        "y_data": "",
        "x_data": "",
        "instruments": "",
        "feature_names": "",
        "instrument_names": ""
    },
    examples=[
        "",
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        "",
        ""
    ]
)


# ============================================================================
#  ( - 3)
# ============================================================================

DATA_CLEANING = ToolDescription(
    name="data_cleaning",
    description="数据清洗工具 - 处理缺失值和异常值",
    field_descriptions={
        "data": "数据字典格式",
        "handle_missing": "缺失值处理方式(drop/mean/median/forward_fill/backward_fill)",
        "handle_outliers": "异常值处理方式(keep/remove/winsorize)",
        "outlier_method": "异常值检测方法(iqr/zscore)",
        "outlier_threshold": "异常值阈值"
    },
    examples=[
        "处理缺失值并删除异常值",
        "填充缺失值并保留异常值"
    ],
    use_cases=[
        "数据预处理",
        "清理导入的原始数据",
        "异常值检测和处理"
    ]
)

DATA_MERGE = ToolDescription(
    name="data_merge",
    description="数据合并工具 - 类似Stata的merge",
    field_descriptions={
        "left_data": "左侧数据集",
        "right_data": "右侧数据集",
        "on": "合并键",
        "how": "合并方式(inner/left/right/outer)"
    },
    examples=[
        "内连接合并两个数据集",
        "左连接保留所有左侧数据"
    ],
    use_cases=[
        "合并多个数据源",
        "匹配实体和时间数据",
        "数据集扩展"
    ]
)

RESHAPE_TO_LONG = ToolDescription(
    name="reshape_to_long",
    description="宽格式→长格式重塑",
    field_descriptions={
        "data": "宽格式数据",
        "id_vars": "标识变量列表",
        "value_vars": "要转换的值列表",
        "var_name": "变量名列名",
        "value_name": "值列名"
    },
    examples=[
        "将多年数据从列转为行",
        "重塑面板数据"
    ],
    use_cases=[
        "面板数据准备",
        "时间序列重塑",
        "重复测量数据转换"
    ]
)

RESHAPE_TO_WIDE = ToolDescription(
    name="reshape_to_wide",
    description="长格式→宽格式重塑",
    field_descriptions={
        "data": "长格式数据",
        "id_var": "标识变量",
        "variable_col": "变量名列",
        "value_col": "值列"
    },
    examples=[
        "将时间序列从行转为列",
        "创建交叉表"
    ],
    use_cases=[
        "时间序列分析准备",
        "创建宽表格式",
        "数据透视"
    ]
)


# ============================================================================
#  ()
# ============================================================================

SCATTER_PLOT = ToolDescription(
    name="scatter_plot",
    description=" - ",
    field_descriptions={
        "x_data": "X",
        "y_data": "Y",
        "x_label": "X",
        "y_label": "Y",
        "title": "",
        "add_regression_line": ""
    },
    examples=[
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)

HISTOGRAM_PLOT = ToolDescription(
    name="histogram_plot",
    description=" - ",
    field_descriptions={
        "data": "",
        "bins": "",
        "label": "",
        "title": "",
        "show_density": ""
    },
    examples=[
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)

CORRELATION_HEATMAP = ToolDescription(
    name="correlation_heatmap",
    description="",
    field_descriptions={
        "data": "",
        "title": "",
        "method": "(pearson/spearman/kendall)"
    },
    examples=[
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)


# ============================================================================
#  ()
# ============================================================================

WLS_REGRESSION = ToolDescription(
    name="wls_regression",
    description="(WLS) - ",
    field_descriptions={
        "y_data": "",
        "x_data": "",
        "weights": "()",
        "weight_type": "(manual/inverse_variance/abs_residuals)",
        "feature_names": ""
    },
    examples=[
        "",
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)

GMM_ESTIMATION = ToolDescription(
    name="gmm_estimation",
    description="(GMM)",
    field_descriptions={
        "y_data": "",
        "x_data": "",
        "instruments": "",
        "feature_names": "",
        "weight_matrix": "(identity/optimal)"
    },
    examples=[
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)

BOOTSTRAP_ANALYSIS = ToolDescription(
    name="bootstrap_analysis",
    description="Bootstrap",
    field_descriptions={
        "data": "",
        "statistic_func": "(mean/median/std/var)",
        "n_bootstrap": "Bootstrap",
        "confidence_level": ""
    },
    examples=[
        "",
        "",
        ""
    ],
    use_cases=[
        "",
        "",
        ""
    ]
)
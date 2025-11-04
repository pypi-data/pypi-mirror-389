"""

"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Any
from pydantic import BaseModel
import statsmodels.api as sm


class DescriptiveStats(BaseModel):
    """"""
    mean: float
    median: float
    std: float
    min: float
    max: float
    skewness: float
    kurtosis: float
    count: int


class CorrelationResult(BaseModel):
    """"""
    correlation_matrix: Dict[str, Dict[str, float]]
    method: str


def calculate_descriptive_stats(data) -> DescriptiveStats:
    """
    计算描述性统计量
    支持两种输入格式：
    1. List[float] - 单个变量的数据列表
    2. Dict[str, List[float]] - 多变量数据字典（会返回第一个变量的统计）
    """
    # 处理不同的输入类型
    if isinstance(data, dict):
        # 如果是字典，取第一个变量的数据
        if not data:
            raise ValueError("数据字典不能为空")
        first_var = next(iter(data.values()))
        arr = np.array(first_var, dtype=float)
    elif isinstance(data, (list, np.ndarray)):
        # 如果是列表或数组，直接使用
        arr = np.array(data, dtype=float)
    else:
        raise TypeError(f"不支持的数据类型: {type(data)}. 期望 List[float] 或 Dict[str, List[float]]")
    
    if len(arr) == 0:
        raise ValueError("数据不能为空")
    
    return DescriptiveStats(
        mean=float(np.mean(arr)),
        median=float(np.median(arr)),
        std=float(np.std(arr)),
        min=float(np.min(arr)),
        max=float(np.max(arr)),
        skewness=float(stats.skew(arr)),
        kurtosis=float(stats.kurtosis(arr)),
        count=len(arr)
    )


def calculate_correlation_matrix(
    data: Dict[str, List[float]],
    method: str = "pearson"
) -> CorrelationResult:
    """"""
    df = pd.DataFrame(data)
    corr_matrix = df.corr(method=method)

    return CorrelationResult(
        correlation_matrix=corr_matrix.to_dict(),
        method=method
    )


def perform_hypothesis_test(
    data1: List[float],
    data2: List[float] = None,
    test_type: str = "t_test",
    alpha: float = 0.05
) -> Dict[str, Any]:
    """"""
    if test_type == "t_test":
        if data2 is None:
            # t
            t_stat, p_value = stats.ttest_1samp(data1, 0)
            test_name = "t"
        else:
            # t
            t_stat, p_value = stats.ttest_ind(data1, data2)
            test_name = "t"

        return {
            "test_type": test_name,
            "statistic": t_stat,
            "p_value": p_value,
            "significant": p_value < alpha,
            "alpha": alpha
        }

    elif test_type == "f_test":
        # F
        if data2 is None:
            raise ValueError("F")

        f_stat, p_value = stats.f_oneway(data1, data2)
        return {
            "test_type": "F",
            "statistic": f_stat,
            "p_value": p_value,
            "significant": p_value < alpha,
            "alpha": alpha
        }

    elif test_type == "chi_square":
        # 
        # 
        chi2_stat, p_value = stats.chisquare(data1)
        return {
            "test_type": "",
            "statistic": chi2_stat,
            "p_value": p_value,
            "significant": p_value < alpha,
            "alpha": alpha
        }

    elif test_type == "adf":
        # ADF
        from statsmodels.tsa.stattools import adfuller
        adf_result = adfuller(data1)
        return {
            "test_type": "ADF",
            "statistic": adf_result[0],
            "p_value": adf_result[1],
            "critical_values": adf_result[4],
            "significant": adf_result[1] < alpha,
            "alpha": alpha
        }
    
    else:
        raise ValueError(f": {test_type}")


def normality_test(data: List[float]) -> Dict[str, Any]:
    """"""
    # Shapiro-Wilk
    shapiro_stat, shapiro_p = stats.shapiro(data)

    # Kolmogorov-Smirnov
    ks_stat, ks_p = stats.kstest(data, 'norm', args=(np.mean(data), np.std(data)))

    return {
        "shapiro_wilk": {
            "statistic": shapiro_stat,
            "p_value": shapiro_p,
            "normal": shapiro_p > 0.05
        },
        "kolmogorov_smirnov": {
            "statistic": ks_stat,
            "p_value": ks_p,
            "normal": ks_p > 0.05
        }
    }
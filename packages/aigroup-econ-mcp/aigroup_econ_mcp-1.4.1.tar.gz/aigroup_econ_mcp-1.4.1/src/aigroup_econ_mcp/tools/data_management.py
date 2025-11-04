"""

Stata
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field
import warnings
warnings.filterwarnings('ignore')


class DataCleaningResult(BaseModel):
    """"""
    cleaned_data: Dict[str, List[float]] = Field(description="")
    n_missing_removed: int = Field(description="")
    n_outliers_removed: int = Field(description="")
    original_size: int = Field(description="")
    cleaned_size: int = Field(description="")
    variables: List[str] = Field(description="")


class DataMergeResult(BaseModel):
    """"""
    merged_data: Dict[str, List] = Field(description="")
    n_matched: int = Field(description="")
    n_unmatched_left: int = Field(description="")
    n_unmatched_right: int = Field(description="")
    merge_type: str = Field(description="")
    key_variable: str = Field(description="")


class DataReshapeResult(BaseModel):
    """"""
    reshaped_data: Dict[str, List] = Field(description="")
    reshape_type: str = Field(description="(wide/long)")
    original_shape: Tuple[int, int] = Field(description="(,)")
    new_shape: Tuple[int, int] = Field(description="(,)")
    id_vars: List[str] = Field(description="ID")
    value_vars: List[str] = Field(description="")


def clean_data(
    data: Dict[str, List[float]],
    handle_missing: str = "drop",
    handle_outliers: str = "keep",
    outlier_method: str = "iqr",
    outlier_threshold: float = 3.0
) -> DataCleaningResult:
    """
    
    
     
    
    
     
    - 
    - IQRZ-score
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        data: 
        handle_missing: ("drop", "mean", "median", "ffill")
        handle_outliers: ("keep", "drop", "cap")
        outlier_method: ("iqr", "zscore")
        outlier_threshold: IQRZ-score
    
    Returns:
        DataCleaningResult: 
    """
    if not data:
        raise ValueError("")
    
    # DataFrame
    df = pd.DataFrame(data)
    original_size = len(df)
    n_missing_removed = 0
    n_outliers_removed = 0
    
    # 
    if handle_missing == "drop":
        df_before = len(df)
        df = df.dropna()
        n_missing_removed = df_before - len(df)
    elif handle_missing == "mean":
        df = df.fillna(df.mean())
    elif handle_missing == "median":
        df = df.fillna(df.median())
    elif handle_missing == "ffill":
        df = df.fillna(method='ffill')
    elif handle_missing == "bfill":
        df = df.fillna(method='bfill')
    
    # 
    if handle_outliers != "keep":
        for col in df.select_dtypes(include=[np.number]).columns:
            if outlier_method == "iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - outlier_threshold * IQR
                upper_bound = Q3 + outlier_threshold * IQR
                
                if handle_outliers == "drop":
                    df_before = len(df)
                    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
                    n_outliers_removed += df_before - len(df)
                elif handle_outliers == "cap":
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
            
            elif outlier_method == "zscore":
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                if handle_outliers == "drop":
                    df_before = len(df)
                    df = df[z_scores < outlier_threshold]
                    n_outliers_removed += df_before - len(df)
                elif handle_outliers == "cap":
                    mean = df[col].mean()
                    std = df[col].std()
                    lower_bound = mean - outlier_threshold * std
                    upper_bound = mean + outlier_threshold * std
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
    
    # 
    cleaned_data = df.to_dict('list')
    
    return DataCleaningResult(
        cleaned_data=cleaned_data,
        n_missing_removed=n_missing_removed,
        n_outliers_removed=n_outliers_removed,
        original_size=original_size,
        cleaned_size=len(df),
        variables=list(cleaned_data.keys())
    )


def merge_data(
    left_data: Dict[str, List],
    right_data: Dict[str, List],
    on: str,
    how: str = "inner"
) -> DataMergeResult:
    """
    Statamerge
    
     
    
    
     
    - inner: 
    - left: 
    - right: 
    - outer: 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        left_data: 
        right_data: 
        on: 
        how: ("inner", "left", "right", "outer")
    
    Returns:
        DataMergeResult: 
    """
    if not left_data or not right_data:
        raise ValueError("")
    
    if on not in left_data:
        raise ValueError(f"'{on}'")
    
    if on not in right_data:
        raise ValueError(f"'{on}'")
    
    # DataFrame
    left_df = pd.DataFrame(left_data)
    right_df = pd.DataFrame(right_data)
    
    # 
    n_left = len(left_df)
    n_right = len(right_df)
    
    # 
    merged_df = pd.merge(left_df, right_df, on=on, how=how, indicator=True)
    
    # 
    if '_merge' in merged_df.columns:
        n_matched = len(merged_df[merged_df['_merge'] == 'both'])
        n_unmatched_left = len(merged_df[merged_df['_merge'] == 'left_only'])
        n_unmatched_right = len(merged_df[merged_df['_merge'] == 'right_only'])
        # _merge
        merged_df = merged_df.drop('_merge', axis=1)
    else:
        n_matched = len(merged_df)
        n_unmatched_left = 0
        n_unmatched_right = 0
    
    # 
    merged_data = merged_df.to_dict('list')
    
    return DataMergeResult(
        merged_data=merged_data,
        n_matched=n_matched,
        n_unmatched_left=n_unmatched_left,
        n_unmatched_right=n_unmatched_right,
        merge_type=how,
        key_variable=on
    )


def append_data(
    data_list: List[Dict[str, List]],
    fill_missing: bool = True
) -> Dict[str, List]:
    """
    Stataappend
    
     
    
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        data_list: 
        fill_missing: NaN
    
    Returns:
        Dict[str, List]: 
    """
    if not data_list:
        raise ValueError("")
    
    if len(data_list) == 1:
        return data_list[0]
    
    # DataFrame
    df_list = [pd.DataFrame(data) for data in data_list]
    
    # 
    if fill_missing:
        # NaN
        appended_df = pd.concat(df_list, ignore_index=True, sort=False)
    else:
        # 
        appended_df = pd.concat(df_list, ignore_index=True, join='inner')
    
    # 
    return appended_df.to_dict('list')


def reshape_wide_to_long(
    data: Dict[str, List],
    id_vars: List[str],
    value_vars: List[str],
    var_name: str = "variable",
    value_name: str = "value"
) -> DataReshapeResult:
    """
    Statareshape long
    
     
    
    
     
    :
    id  y2020  y2021  y2022
    1   100    110    120
    2   200    210    220
    
    :
    id  variable  value
    1   y2020     100
    1   y2021     110
    1   y2022     120
    2   y2020     200
    ...
    
     
    - 
    - 
    - 
    
     
    - ID
    - 
    
    Args:
        data: 
        id_vars: ID
        value_vars: 
        var_name: 
        value_name: 
    
    Returns:
        DataReshapeResult: 
    """
    if not data:
        raise ValueError("")
    
    df = pd.DataFrame(data)
    original_shape = df.shape
    
    # 
    for var in id_vars:
        if var not in df.columns:
            raise ValueError(f"ID'{var}'")
    
    for var in value_vars:
        if var not in df.columns:
            raise ValueError(f"'{var}'")
    
    # 
    reshaped_df = pd.melt(
        df,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name=var_name,
        value_name=value_name
    )
    
    new_shape = reshaped_df.shape
    reshaped_data = reshaped_df.to_dict('list')
    
    return DataReshapeResult(
        reshaped_data=reshaped_data,
        reshape_type="wide_to_long",
        original_shape=original_shape,
        new_shape=new_shape,
        id_vars=id_vars,
        value_vars=value_vars
    )


def reshape_long_to_wide(
    data: Dict[str, List],
    id_var: str,
    variable_col: str,
    value_col: str
) -> DataReshapeResult:
    """
    Statareshape wide
    
     
    
    
     
    :
    id  year  value
    1   2020  100
    1   2021  110
    2   2020  200
    2   2021  210
    
    :
    id  value_2020  value_2021
    1   100         110
    2   200         210
    
     
    - 
    - 
    - 
    
     
    - ID
    - 
    
    Args:
        data: 
        id_var: ID
        variable_col: 
        value_col: 
    
    Returns:
        DataReshapeResult: 
    """
    if not data:
        raise ValueError("")
    
    df = pd.DataFrame(data)
    original_shape = df.shape
    
    # 
    for col in [id_var, variable_col, value_col]:
        if col not in df.columns:
            raise ValueError(f"'{col}'")
    
    # 
    reshaped_df = df.pivot(
        index=id_var,
        columns=variable_col,
        values=value_col
    ).reset_index()
    
    # 
    reshaped_df.columns.name = None
    
    new_shape = reshaped_df.shape
    reshaped_data = reshaped_df.to_dict('list')
    
    return DataReshapeResult(
        reshaped_data=reshaped_data,
        reshape_type="long_to_wide",
        original_shape=original_shape,
        new_shape=new_shape,
        id_vars=[id_var],
        value_vars=[value_col]
    )


def generate_variable(
    data: Dict[str, List],
    new_var_name: str,
    expression: str = None,
    function: str = None,
    source_vars: List[str] = None
) -> Dict[str, List]:
    """
    Statagenerate
    
     
    
    
     
    - "sum": 
    - "mean": 
    - "diff": 
    - "product": 
    - "ratio": 
    - "log": 
    - "exp": 
    - "square": 
    - "sqrt": 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        data: 
        new_var_name: 
        expression: 
        function: 
        source_vars: 
    
    Returns:
        Dict[str, List]: 
    """
    if not data:
        raise ValueError("")
    
    if new_var_name in data:
        raise ValueError(f"'{new_var_name}'")
    
    df = pd.DataFrame(data)
    
    # 
    if source_vars:
        for var in source_vars:
            if var not in df.columns:
                raise ValueError(f"'{var}'")
    
    # 
    if function == "sum":
        df[new_var_name] = df[source_vars].sum(axis=1)
    elif function == "mean":
        df[new_var_name] = df[source_vars].mean(axis=1)
    elif function == "diff":
        if len(source_vars) != 2:
            raise ValueError("diff2")
        df[new_var_name] = df[source_vars[0]] - df[source_vars[1]]
    elif function == "product":
        df[new_var_name] = df[source_vars].prod(axis=1)
    elif function == "ratio":
        if len(source_vars) != 2:
            raise ValueError("ratio2")
        df[new_var_name] = df[source_vars[0]] / df[source_vars[1]]
    elif function == "log":
        if len(source_vars) != 1:
            raise ValueError("log1")
        df[new_var_name] = np.log(df[source_vars[0]])
    elif function == "exp":
        if len(source_vars) != 1:
            raise ValueError("exp1")
        df[new_var_name] = np.exp(df[source_vars[0]])
    elif function == "square":
        if len(source_vars) != 1:
            raise ValueError("square1")
        df[new_var_name] = df[source_vars[0]] ** 2
    elif function == "sqrt":
        if len(source_vars) != 1:
            raise ValueError("sqrt1")
        df[new_var_name] = np.sqrt(df[source_vars[0]])
    else:
        raise ValueError(f": {function}")
    
    return df.to_dict('list')


def drop_variables(
    data: Dict[str, List],
    vars_to_drop: List[str]
) -> Dict[str, List]:
    """
    Statadrop
    
     
    
    
     
    - 
    - 
    - 
    
    Args:
        data: 
        vars_to_drop: 
    
    Returns:
        Dict[str, List]: 
    """
    if not data:
        raise ValueError("")
    
    df = pd.DataFrame(data)
    
    # 
    for var in vars_to_drop:
        if var not in df.columns:
            raise ValueError(f"'{var}'")
    
    # 
    df = df.drop(columns=vars_to_drop)
    
    return df.to_dict('list')


def keep_variables(
    data: Dict[str, List],
    vars_to_keep: List[str]
) -> Dict[str, List]:
    """
    Statakeep
    
     
    
    
     
    - 
    - 
    - 
    
    Args:
        data: 
        vars_to_keep: 
    
    Returns:
        Dict[str, List]: 
    """
    if not data:
        raise ValueError("")
    
    df = pd.DataFrame(data)
    
    # 
    for var in vars_to_keep:
        if var not in df.columns:
            raise ValueError(f"'{var}'")
    
    # 
    df = df[vars_to_keep]
    
    return df.to_dict('list')
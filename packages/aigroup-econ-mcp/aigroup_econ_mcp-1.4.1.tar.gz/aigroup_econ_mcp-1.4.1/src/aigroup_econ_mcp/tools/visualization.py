"""

Stata
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field
import io
import base64
import warnings
warnings.filterwarnings('ignore')

# 
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class PlotResult(BaseModel):
    """"""
    plot_type: str = Field(description="")
    image_base64: str = Field(description="Base64")
    description: str = Field(description="")
    n_observations: int = Field(description="")
    variables: List[str] = Field(description="")


def _figure_to_base64(fig) -> str:
    """matplotlibbase64"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return img_base64


def scatter_plot(
    x_data: List[float],
    y_data: List[float],
    x_label: str = "X",
    y_label: str = "Y",
    title: str = "",
    add_regression_line: bool = True,
    color: str = "blue",
    alpha: float = 0.6
) -> PlotResult:
    """
    Scatter Plot
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    
    Args:
        x_data: X
        y_data: Y
        x_label: X
        y_label: Y
        title: 
        add_regression_line: 
        color: 
        alpha: (0-1)
    
    Returns:
        PlotResult: 
    """
    if not x_data or not y_data:
        raise ValueError("XY")
    
    if len(x_data) != len(y_data):
        raise ValueError(f"XY: {len(x_data)} vs {len(y_data)}")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 
    ax.scatter(x_data, y_data, color=color, alpha=alpha, s=50)
    
    # 
    if add_regression_line:
        z = np.polyfit(x_data, y_data, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(x_data), max(x_data), 100)
        ax.plot(x_line, p(x_line), "r--", linewidth=2, label=f': y={z[0]:.2f}x+{z[1]:.2f}')
        ax.legend()
    
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # 
    corr = np.corrcoef(x_data, y_data)[0, 1]
    description = f"{x_label}{y_label}={corr:.3f}"
    
    img_base64 = _figure_to_base64(fig)
    
    return PlotResult(
        plot_type="scatter",
        image_base64=img_base64,
        description=description,
        n_observations=len(x_data),
        variables=[x_label, y_label]
    )


def histogram(
    data: List[float],
    bins: int = 30,
    label: str = "",
    title: str = "",
    show_density: bool = True,
    color: str = "skyblue",
    edgecolor: str = "black"
) -> PlotResult:
    """
    Histogram
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    
    Args:
        data: 
        bins: 
        label: 
        title: 
        show_density: 
        color: 
        edgecolor: 
    
    Returns:
        PlotResult: 
    """
    if not data:
        raise ValueError("")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 
    n, bins_edges, patches = ax.hist(
        data, bins=bins, density=show_density,
        color=color, edgecolor=edgecolor, alpha=0.7
    )
    
    # 
    if show_density:
        from scipy import stats
        kde = stats.gaussian_kde(data)
        x_range = np.linspace(min(data), max(data), 200)
        ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='')
        ax.legend()
    
    ax.set_xlabel(label, fontsize=12)
    ax.set_ylabel('' if not show_density else '', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 
    mean_val = np.mean(data)
    std_val = np.std(data)
    ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'={mean_val:.2f}')
    
    description = f"{label}={mean_val:.3f}={std_val:.3f}"
    
    img_base64 = _figure_to_base64(fig)
    
    return PlotResult(
        plot_type="histogram",
        image_base64=img_base64,
        description=description,
        n_observations=len(data),
        variables=[label]
    )


def box_plot(
    data: Union[List[float], Dict[str, List[float]]],
    labels: Optional[List[str]] = None,
    title: str = "",
    ylabel: str = "",
    orientation: str = "vertical"
) -> PlotResult:
    """
    Box Plot
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    
    Args:
        data: 
        labels: data
        title: 
        ylabel: Y
        orientation: ("vertical""horizontal")
    
    Returns:
        PlotResult: 
    """
    if not data:
        raise ValueError("")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 
    if isinstance(data, dict):
        data_list = list(data.values())
        if labels is None:
            labels = list(data.keys())
        n_obs = sum(len(d) for d in data_list)
        var_names = labels
    else:
        data_list = [data]
        if labels is None:
            labels = [""]
        n_obs = len(data)
        var_names = labels
    
    # 
    bp = ax.boxplot(
        data_list,
        labels=labels,
        patch_artist=True,
        vert=(orientation == "vertical"),
        showmeans=True
    )
    
    # 
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    
    for whisker in bp['whiskers']:
        whisker.set(color='#7570b3', linewidth=1.5)
    
    for cap in bp['caps']:
        cap.set(color='#7570b3', linewidth=1.5)
    
    for median in bp['medians']:
        median.set(color='red', linewidth=2)
    
    for mean in bp['means']:
        mean.set(marker='D', markerfacecolor='green', markersize=8)
    
    if orientation == "vertical":
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xlabel("", fontsize=12)
    else:
        ax.set_xlabel(ylabel, fontsize=12)
        ax.set_ylabel("", fontsize=12)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y' if orientation == "vertical" else 'x')
    
    description = f"{''.join(var_names)}"
    
    img_base64 = _figure_to_base64(fig)
    
    return PlotResult(
        plot_type="boxplot",
        image_base64=img_base64,
        description=description,
        n_observations=n_obs,
        variables=var_names
    )


def line_plot(
    data: Union[List[float], Dict[str, List[float]]],
    x_data: Optional[List] = None,
    labels: Optional[List[str]] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    markers: bool = True
) -> PlotResult:
    """
    Line Plot
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    
    Args:
        data: 
        x_data: X
        labels: 
        title: 
        xlabel: X
        ylabel: Y
        markers: 
    
    Returns:
        PlotResult: 
    """
    if not data:
        raise ValueError("")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 
    if isinstance(data, dict):
        data_dict = data
        if labels is None:
            labels = list(data.keys())
        n_obs = len(next(iter(data.values())))
        var_names = labels
    else:
        data_dict = {"": data}
        if labels is None:
            labels = [""]
        n_obs = len(data)
        var_names = labels
    
    # X
    if x_data is None:
        x_data = list(range(1, n_obs + 1))
    
    # 
    marker_style = 'o' if markers else None
    for i, (label, y_data) in enumerate(data_dict.items()):
        ax.plot(x_data, y_data, marker=marker_style, linewidth=2, 
                markersize=6, label=label, alpha=0.8)
    
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    if len(data_dict) > 1:
        ax.legend(fontsize=10)
    
    description = f"{''.join(var_names)}"
    
    img_base64 = _figure_to_base64(fig)
    
    return PlotResult(
        plot_type="line",
        image_base64=img_base64,
        description=description,
        n_observations=n_obs,
        variables=var_names
    )


def bar_plot(
    data: Union[List[float], Dict[str, List[float]]],
    labels: Optional[List[str]] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    orientation: str = "vertical",
    color: Union[str, List[str]] = "steelblue"
) -> PlotResult:
    """
    Bar Plot
    
     
    
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    
    Args:
        data: 
        labels: 
        title: 
        xlabel: X
        ylabel: Y
        orientation: ("vertical""horizontal")
        color: 
    
    Returns:
        PlotResult: 
    """
    if not data:
        raise ValueError("")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 
    if isinstance(data, dict):
        categories = list(data.keys())
        values = list(data.values())
        if isinstance(values[0], list):
            # 
            n_obs = sum(len(v) for v in values)
            var_names = categories
        else:
            # 
            n_obs = len(values)
            var_names = [title]
    else:
        if labels is None:
            categories = [f"Cat{i+1}" for i in range(len(data))]
        else:
            categories = labels
        values = data
        n_obs = len(data)
        var_names = [title]
    
    # 
    if orientation == "vertical":
        bars = ax.bar(categories, values, color=color, alpha=0.7, edgecolor='black')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        # 
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    else:
        bars = ax.barh(categories, values, color=color, alpha=0.7, edgecolor='black')
        ax.set_ylabel(xlabel, fontsize=12)
        ax.set_xlabel(ylabel, fontsize=12)
        # 
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{width:.2f}', ha='left', va='center', fontsize=9)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y' if orientation == "vertical" else 'x')
    
    description = f"{''.join(var_names)}"
    
    img_base64 = _figure_to_base64(fig)
    
    return PlotResult(
        plot_type="bar",
        image_base64=img_base64,
        description=description,
        n_observations=n_obs,
        variables=var_names
    )


def correlation_matrix_plot(
    data: Dict[str, List[float]],
    title: str = "",
    method: str = "pearson",
    annot: bool = True,
    cmap: str = "coolwarm"
) -> PlotResult:
    """
    
    
     
    
    
     
    - 
    - 1
    - 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    
    Args:
        data: 
        title: 
        method: ("pearson", "spearman", "kendall")
        annot: 
        cmap: 
    
    Returns:
        PlotResult: 
    """
    if not data:
        raise ValueError("")
    
    # DataFrame
    import pandas as pd
    df = pd.DataFrame(data)
    
    # 
    corr_matrix = df.corr(method=method)
    
    # 
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 
    sns.heatmap(
        corr_matrix,
        annot=annot,
        fmt='.3f',
        cmap=cmap,
        center=0,
        square=True,
        linewidths=1,
        cbar_kws={"shrink": 0.8},
        ax=ax,
        vmin=-1, vmax=1
    )
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    description = f"{method}{len(data)}"
    var_names = list(data.keys())
    n_obs = len(next(iter(data.values())))
    
    img_base64 = _figure_to_base64(fig)
    
    return PlotResult(
        plot_type="correlation_matrix",
        image_base64=img_base64,
        description=description,
        n_observations=n_obs,
        variables=var_names
    )


def regression_diagnostic_plot(
    y_true: List[float],
    y_pred: List[float],
    residuals: List[float],
    title: str = ""
) -> PlotResult:
    """
    
    
     
    
    
     
    1. vs
    2. Q-Q
    3. vs
    4. 
    
     
    - 
    - 
    - 
    
     
    - 
    - 
    - 
    
    Args:
        y_true: 
        y_pred: 
        residuals: 
        title: 
    
    Returns:
        PlotResult: 
    """
    if not y_true or not y_pred or not residuals:
        raise ValueError("")
    
    if len(y_true) != len(y_pred) or len(y_true) != len(residuals):
        raise ValueError("")
    
    # 2x2
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    # 1:  vs 
    axes[0, 0].scatter(y_pred, residuals, alpha=0.6, color='blue')
    axes[0, 0].axhline(y=0, color='r', linestyle='--', linewidth=2)
    axes[0, 0].set_xlabel('', fontsize=11)
    axes[0, 0].set_ylabel('', fontsize=11)
    axes[0, 0].set_title(' vs ', fontsize=12)
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2: Q-Q
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=axes[0, 1])
    axes[0, 1].set_title('Q-Q', fontsize=12)
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3:  vs 
    axes[1, 0].scatter(y_true, y_pred, alpha=0.6, color='green')
    # 
    min_val = min(min(y_true), min(y_pred))
    max_val = max(max(y_true), max(y_pred))
    axes[1, 0].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)
    axes[1, 0].set_xlabel('', fontsize=11)
    axes[1, 0].set_ylabel('', fontsize=11)
    axes[1, 0].set_title(' vs ', fontsize=12)
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4: 
    axes[1, 1].hist(residuals, bins=30, color='skyblue', edgecolor='black', alpha=0.7, density=True)
    # 
    mu, sigma = np.mean(residuals), np.std(residuals)
    x = np.linspace(min(residuals), max(residuals), 100)
    axes[1, 1].plot(x, stats.norm.pdf(x, mu, sigma), 'r-', linewidth=2, label='')
    axes[1, 1].set_xlabel('', fontsize=11)
    axes[1, 1].set_ylabel('', fontsize=11)
    axes[1, 1].set_title('', fontsize=12)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    description = f"={len(y_true)}"
    
    img_base64 = _figure_to_base64(fig)
    
    return PlotResult(
        plot_type="regression_diagnostic",
        image_base64=img_base64,
        description=description,
        n_observations=len(y_true),
        variables=["y_true", "y_pred", "residuals"]
    )
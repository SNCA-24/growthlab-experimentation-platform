from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from core.contracts.metric_contracts import MetricContract
from core.contracts._common import MetricType, NullFillStrategy, OutlierHandling


@dataclass(slots=True)
class GroupStats:
    n: int
    numerator_sum: float
    denominator_sum: float
    estimate: float
    variance: float | None = None
    std: float | None = None


@dataclass(slots=True)
class InferenceSummary:
    total_n: int
    mature_n: int
    immature_n: int
    analyzed_n: int
    status: str
    denominator_label: str
    control: GroupStats
    treatment: GroupStats
    effect: float
    standard_error: float
    ci_lower: float
    ci_upper: float
    p_value: float
    relative_lift: float | None
    cuped_enabled: bool
    cuped_theta: float | None
    cuped_control: GroupStats | None
    cuped_treatment: GroupStats | None
    cuped_effect: float | None
    cuped_standard_error: float | None
    cuped_ci_lower: float | None
    cuped_ci_upper: float | None
    cuped_p_value: float | None
    cuped_relative_lift: float | None
    cuped_reason: str | None
    practical_threshold_value: float | None
    practical_threshold_type: str | None
    practical_threshold_met: bool | None
    practical_threshold_evaluable: bool | None
    mde_at_target_power: float | None
    alpha: float
    target_power: float
    notes: str | None = None


def _as_float_series(values: pd.Series | np.ndarray | list[Any]) -> pd.Series:
    return pd.Series(values, dtype="float64")


def maybe_apply_null_fill(values: pd.Series, metric: MetricContract) -> pd.Series:
    series = values.copy()
    if metric.null_fill_strategy == NullFillStrategy.zero:
        return series.fillna(0.0)
    return series


def apply_metric_transforms(values: pd.Series, metric: MetricContract) -> pd.Series:
    series = _as_float_series(values)
    series = maybe_apply_null_fill(series, metric)

    upper_clip: float | None = None
    if metric.outlier_handling == OutlierHandling.winsorize_p99 or metric.winsorization == "p99":
        finite = series[np.isfinite(series)]
        if len(finite) > 0:
            upper_clip = float(np.quantile(finite.to_numpy(), 0.99))
    if upper_clip is not None:
        series = series.clip(upper=upper_clip)
    if metric.outlier_handling == OutlierHandling.clip_nonnegative:
        series = series.clip(lower=0.0)
    return series


def align_analysis_frame(
    metric: MetricContract,
    y: pd.Series,
    covariate: pd.Series | None = None,
) -> tuple[pd.Series, pd.Series | None]:
    y_series = apply_metric_transforms(y, metric)
    x_series = None
    if covariate is not None:
        x_series = apply_metric_transforms(covariate, metric)

    if metric.null_fill_strategy == NullFillStrategy.zero:
        if x_series is not None:
            return y_series.fillna(0.0), x_series.fillna(0.0)
        return y_series.fillna(0.0), None

    mask = y_series.notna()
    if x_series is not None:
        mask &= x_series.notna()
    y_series = y_series.loc[mask]
    if x_series is not None:
        x_series = x_series.loc[mask]
    return y_series, x_series


def group_stats(
    numerator: pd.Series | np.ndarray,
    denominator: pd.Series | np.ndarray,
    *,
    force_ratio: bool = False,
) -> GroupStats:
    num = _as_float_series(numerator).to_numpy(dtype=np.float64)
    den = _as_float_series(denominator).to_numpy(dtype=np.float64)
    n = int(len(num))
    numerator_sum = float(np.nansum(num))
    denominator_sum = float(np.nansum(den))
    if force_ratio or denominator_sum != 0:
        estimate = float(numerator_sum / denominator_sum) if denominator_sum != 0 else float("nan")
    else:
        estimate = float("nan")
    variance = None
    std = None
    return GroupStats(
        n=n,
        numerator_sum=numerator_sum,
        denominator_sum=denominator_sum,
        estimate=estimate,
        variance=variance,
        std=std,
    )


def ratio_group_estimate_and_se(
    numerator: pd.Series | np.ndarray,
    denominator: pd.Series | np.ndarray,
) -> tuple[float, float, float, float, float]:
    x = _as_float_series(numerator).to_numpy(dtype=np.float64)
    y = _as_float_series(denominator).to_numpy(dtype=np.float64)
    n = len(x)
    if n < 2:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")
    if np.any(~np.isfinite(x)) or np.any(~np.isfinite(y)):
        mask = np.isfinite(x) & np.isfinite(y)
        x = x[mask]
        y = y[mask]
        n = len(x)
        if n < 2:
            return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")

    mx = float(np.mean(x))
    my = float(np.mean(y))
    if my <= 0:
        return float("nan"), float("nan"), mx, my, float("nan")

    var_x = float(np.var(x, ddof=1)) if n > 1 else 0.0
    var_y = float(np.var(y, ddof=1)) if n > 1 else 0.0
    cov_xy = float(np.cov(x, y, ddof=1)[0, 1]) if n > 1 else 0.0
    ratio = mx / my
    var_ratio = (var_x / (my**2) + (mx**2) * var_y / (my**4) - 2.0 * mx * cov_xy / (my**3)) / n
    se = sqrt(max(var_ratio, 0.0))
    return ratio, se, mx, my, float(var_ratio)


def _welch_df(var_c: float, n_c: int, var_t: float, n_t: int) -> float:
    a = var_c / n_c
    b = var_t / n_t
    numerator = (a + b) ** 2
    denominator = 0.0
    if n_c > 1 and a > 0:
        denominator += (a**2) / (n_c - 1)
    if n_t > 1 and b > 0:
        denominator += (b**2) / (n_t - 1)
    if denominator <= 0:
        return float("nan")
    return numerator / denominator


def welch_inference_from_groups(
    control: np.ndarray,
    treatment: np.ndarray,
    alpha: float,
) -> tuple[GroupStats, GroupStats, float, float, float, float, float]:
    control = np.asarray(control, dtype=np.float64)
    treatment = np.asarray(treatment, dtype=np.float64)
    c_n = len(control)
    t_n = len(treatment)
    c_sum = float(np.sum(control))
    t_sum = float(np.sum(treatment))
    c_mean = float(np.mean(control)) if c_n else float("nan")
    t_mean = float(np.mean(treatment)) if t_n else float("nan")
    c_var = float(np.var(control, ddof=1)) if c_n > 1 else 0.0
    t_var = float(np.var(treatment, ddof=1)) if t_n > 1 else 0.0
    c_std = float(np.std(control, ddof=1)) if c_n > 1 else 0.0
    t_std = float(np.std(treatment, ddof=1)) if t_n > 1 else 0.0
    effect = t_mean - c_mean
    se = sqrt(max(c_var / max(c_n, 1) + t_var / max(t_n, 1), 0.0))
    df = _welch_df(c_var, max(c_n, 1), t_var, max(t_n, 1))
    if np.isfinite(df) and df > 0 and se > 0:
        crit = stats.t.ppf(1 - alpha / 2.0, df)
        p_value = float(2.0 * (1.0 - stats.t.cdf(abs(effect / se), df)))
    else:
        crit = stats.norm.ppf(1 - alpha / 2.0)
        p_value = float(2.0 * (1.0 - stats.norm.cdf(abs(effect / se)))) if se > 0 else 1.0
    ci_lower = effect - crit * se
    ci_upper = effect + crit * se
    return (
        GroupStats(c_n, c_sum, float(c_n), c_mean, c_var, c_std),
        GroupStats(t_n, t_sum, float(t_n), t_mean, t_var, t_std),
        effect,
        se,
        ci_lower,
        ci_upper,
        p_value,
    )


def ratio_delta_inference_from_groups(
    control_num: np.ndarray,
    control_den: np.ndarray,
    treatment_num: np.ndarray,
    treatment_den: np.ndarray,
    alpha: float,
) -> tuple[GroupStats, GroupStats, float, float, float, float, float, float, float, float]:
    c_ratio, c_se, c_mean_num, c_mean_den, c_var_ratio = ratio_group_estimate_and_se(control_num, control_den)
    t_ratio, t_se, t_mean_num, t_mean_den, t_var_ratio = ratio_group_estimate_and_se(treatment_num, treatment_den)
    c_group = GroupStats(
        n=len(control_num),
        numerator_sum=float(np.sum(control_num)),
        denominator_sum=float(np.sum(control_den)),
        estimate=c_ratio,
        variance=c_var_ratio,
        std=sqrt(max(c_var_ratio, 0.0)) if np.isfinite(c_var_ratio) else None,
    )
    t_group = GroupStats(
        n=len(treatment_num),
        numerator_sum=float(np.sum(treatment_num)),
        denominator_sum=float(np.sum(treatment_den)),
        estimate=t_ratio,
        variance=t_var_ratio,
        std=sqrt(max(t_var_ratio, 0.0)) if np.isfinite(t_var_ratio) else None,
    )
    effect = t_ratio - c_ratio
    se = sqrt(max(c_se**2 + t_se**2, 0.0))
    crit = stats.norm.ppf(1 - alpha / 2.0)
    p_value = float(2.0 * (1.0 - stats.norm.cdf(abs(effect / se)))) if se > 0 else 1.0
    ci_lower = effect - crit * se
    ci_upper = effect + crit * se
    return (
        c_group,
        t_group,
        effect,
        se,
        ci_lower,
        ci_upper,
        p_value,
        c_ratio,
        t_ratio,
        float(se),
    )


def cuped_adjust(y: pd.Series, x: pd.Series) -> tuple[pd.Series, float | None, str | None]:
    frame = pd.DataFrame({"y": y, "x": x}).dropna()
    if len(frame) < 2:
        return y.copy(), None, "cuped_disabled_insufficient_rows"

    x_values = frame["x"].to_numpy(dtype=np.float64)
    y_values = frame["y"].to_numpy(dtype=np.float64)
    x_var = float(np.var(x_values, ddof=1)) if len(frame) > 1 else 0.0
    if not np.isfinite(x_var) or x_var <= 1e-12:
        return y.copy(), None, "cuped_disabled_constant_covariate"

    cov_xy = float(np.cov(x_values, y_values, ddof=1)[0, 1])
    theta = cov_xy / x_var
    x_centered = x_values - float(np.mean(x_values))
    adjusted = y.copy()
    adjusted.loc[frame.index] = y_values - theta * x_centered
    return adjusted, theta, None


def practical_threshold_to_absolute(metric: MetricContract, control_mean: float) -> float:
    threshold = float(metric.practical_significance_threshold)
    if metric.practical_significance_threshold_type is None:
        raise ValueError(f"metric '{metric.metric_name}' is missing practical_significance_threshold_type")
    if metric.practical_significance_threshold_type.value == "absolute":
        return threshold
    return abs(control_mean) * threshold


def evaluate_practical_threshold(
    metric: MetricContract,
    raw_control_mean: float,
    standard_error: float,
    alpha: float,
    target_power: float,
    effect: float,
) -> tuple[float, bool, bool, float]:
    practical_abs = practical_threshold_to_absolute(metric, raw_control_mean)
    z_alpha = stats.norm.ppf(1 - alpha / 2.0)
    z_power = stats.norm.ppf(target_power)
    mde = (z_alpha + z_power) * standard_error
    evaluable = bool(practical_abs >= mde) if np.isfinite(mde) else False
    if metric.direction.value == "higher_is_better":
        met = effect >= practical_abs
    else:
        met = effect <= -practical_abs
    return practical_abs, met, evaluable, float(mde)

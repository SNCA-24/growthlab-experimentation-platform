from __future__ import annotations

import pandas as pd

from core.contracts._common import MetricType
from core.contracts.experiment_contracts import ExperimentContract
from core.contracts.metric_contracts import MetricContract

from .._stats import (
    InferenceSummary,
    align_analysis_frame,
    evaluate_practical_threshold,
    ratio_delta_inference_from_groups,
)
from ..estimands.resolve_population import resolve_population
from ..maturity.filtering import filter_by_maturity
from ..sequential.status import classify_read_status


def analyze_ratio_metric(
    experiment: ExperimentContract,
    metric: MetricContract,
    outcomes: pd.DataFrame,
    *,
    metric_role: str,
    alpha: float,
    target_power: float,
) -> InferenceSummary:
    if metric.metric_type != MetricType.ratio:
        raise TypeError(f"metric '{metric.metric_name}' is not ratio")
    if metric.numerator_column is None or metric.denominator_column is None:
        raise ValueError(f"ratio metric '{metric.metric_name}' requires numerator_column and denominator_column")

    maturity = filter_by_maturity(outcomes, metric)
    population = maturity.filtered.reset_index(drop=True)
    resolved = resolve_population(experiment, population)
    analysis = population.loc[resolved.mask].reset_index(drop=True)

    if metric.numerator_column not in analysis.columns:
        raise ValueError(f"ratio metric '{metric.metric_name}' is missing numerator column '{metric.numerator_column}'")
    if metric.denominator_column not in analysis.columns:
        raise ValueError(f"ratio metric '{metric.metric_name}' is missing denominator column '{metric.denominator_column}'")

    numerator = analysis[metric.numerator_column]
    denominator = analysis[metric.denominator_column]
    numerator, denominator = align_analysis_frame(metric, numerator, denominator)
    analysis = analysis.loc[numerator.index].reset_index(drop=True)
    analysis[metric.numerator_column] = numerator.to_numpy()
    analysis[metric.denominator_column] = denominator.to_numpy()

    group = analysis["assigned_group"].astype(str)
    control_mask = group.eq("control")
    treatment_mask = group.eq("treatment")
    if not control_mask.any() or not treatment_mask.any():
        raise ValueError(f"metric '{metric.metric_name}' requires both control and treatment observations")

    (
        control,
        treatment,
        effect,
        se,
        ci_lower,
        ci_upper,
        p_value,
        _,
        _,
        _,
    ) = ratio_delta_inference_from_groups(
        analysis.loc[control_mask, metric.numerator_column].to_numpy(),
        analysis.loc[control_mask, metric.denominator_column].to_numpy(),
        analysis.loc[treatment_mask, metric.numerator_column].to_numpy(),
        analysis.loc[treatment_mask, metric.denominator_column].to_numpy(),
        alpha,
    )

    control_estimate = control.estimate
    relative_lift = effect / control_estimate if control_estimate not in (0, 0.0) else None
    practical_value, practical_met, evaluable, mde = evaluate_practical_threshold(
        metric,
        control_estimate,
        se,
        alpha,
        target_power,
        effect,
    )

    cuped_enabled = False
    cuped_theta = None
    cuped_control = None
    cuped_treatment = None
    cuped_effect = None
    cuped_se = None
    cuped_ci_lower = None
    cuped_ci_upper = None
    cuped_p_value = None
    cuped_relative_lift = None
    cuped_reason = "cuped_disabled_not_supported_for_ratio_metrics"

    return InferenceSummary(
        total_n=maturity.total_n,
        mature_n=maturity.mature_n,
        immature_n=maturity.immature_n,
        analyzed_n=len(analysis),
        status=classify_read_status(mature_n=maturity.mature_n, immature_n=maturity.immature_n),
        denominator_label=resolved.denominator_label,
        control=control,
        treatment=treatment,
        effect=effect,
        standard_error=se,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_value=p_value,
        relative_lift=relative_lift,
        cuped_enabled=cuped_enabled,
        cuped_theta=cuped_theta,
        cuped_control=cuped_control,
        cuped_treatment=cuped_treatment,
        cuped_effect=cuped_effect,
        cuped_standard_error=cuped_se,
        cuped_ci_lower=cuped_ci_lower,
        cuped_ci_upper=cuped_ci_upper,
        cuped_p_value=cuped_p_value,
        cuped_relative_lift=cuped_relative_lift,
        cuped_reason=cuped_reason,
        practical_threshold_value=practical_value,
        practical_threshold_type=metric.practical_significance_threshold_type.value if metric.practical_significance_threshold_type else None,
        practical_threshold_met=practical_met,
        practical_threshold_evaluable=evaluable,
        mde_at_target_power=mde,
        alpha=alpha,
        target_power=target_power,
    )

from __future__ import annotations

import pandas as pd

from core.contracts._common import MetricType
from core.contracts.experiment_contracts import ExperimentContract
from core.contracts.metric_contracts import MetricContract

from .._stats import (
    InferenceSummary,
    align_analysis_frame,
    evaluate_practical_threshold,
    welch_inference_from_groups,
    cuped_adjust,
)
from ..estimands.resolve_population import resolve_population
from ..maturity.filtering import filter_by_maturity
from ..sequential.status import classify_read_status


def analyze_binary_metric(
    experiment: ExperimentContract,
    metric: MetricContract,
    outcomes: pd.DataFrame,
    *,
    metric_role: str,
    alpha: float,
    target_power: float,
) -> InferenceSummary:
    if metric.metric_type != MetricType.binary:
        raise TypeError(f"metric '{metric.metric_name}' is not binary")
    if metric.metric_column is None:
        raise ValueError(f"metric '{metric.metric_name}' is missing metric_column")

    maturity = filter_by_maturity(outcomes, metric)
    population = maturity.filtered.reset_index(drop=True)
    resolved = resolve_population(experiment, population)
    analysis = population.loc[resolved.mask].reset_index(drop=True)

    y = analysis[metric.metric_column]
    covariate = analysis.get(metric.covariate_column) if metric.covariate_column else None
    y, covariate = align_analysis_frame(metric, y, covariate)
    analysis = analysis.loc[y.index].reset_index(drop=True)
    analysis[metric.metric_column] = y.to_numpy()
    if covariate is not None and metric.covariate_column is not None:
        analysis[metric.covariate_column] = covariate.to_numpy()

    group = analysis["assigned_group"].astype(str)
    control_mask = group.eq("control")
    treatment_mask = group.eq("treatment")
    if not control_mask.any() or not treatment_mask.any():
        raise ValueError(f"metric '{metric.metric_name}' requires both control and treatment observations")

    control, treatment, effect, se, ci_lower, ci_upper, p_value = welch_inference_from_groups(
        analysis.loc[control_mask, metric.metric_column].to_numpy(),
        analysis.loc[treatment_mask, metric.metric_column].to_numpy(),
        alpha,
    )

    relative_lift = effect / control.estimate if control.estimate not in (0, 0.0) else None
    practical_value, practical_met, evaluable, mde = evaluate_practical_threshold(
        metric,
        control.estimate,
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
    cuped_reason = None
    if metric.covariate_column:
        if metric.covariate_column not in analysis.columns:
            cuped_reason = f"cuped_disabled_missing_covariate:{metric.covariate_column}"
        else:
            adjusted, theta, reason = cuped_adjust(analysis[metric.metric_column], analysis[metric.covariate_column])
            if theta is not None and reason is None:
                cuped_enabled = True
                cuped_theta = theta
                cuped_control, cuped_treatment, cuped_effect, cuped_se, cuped_ci_lower, cuped_ci_upper, cuped_p_value = welch_inference_from_groups(
                    adjusted.loc[control_mask].to_numpy(),
                    adjusted.loc[treatment_mask].to_numpy(),
                    alpha,
                )
                cuped_relative_lift = cuped_effect / cuped_control.estimate if cuped_control.estimate not in (0, 0.0) else None
            else:
                cuped_reason = reason

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

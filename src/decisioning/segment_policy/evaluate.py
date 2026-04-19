from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from math import sqrt
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from analysis.ab.binary import analyze_binary_metric
from analysis.ab.continuous import analyze_continuous_metric
from analysis.ratios.delta_method import analyze_ratio_metric
from analysis._stats import InferenceSummary
from core.contracts import MetricContract, MetricType, PolicyContract
from core.contracts._common import DecisionAction, MetricDirection


@dataclass(slots=True)
class SegmentCandidate:
    segment_key: str
    segment_values: dict[str, Any]
    analyzed_n: int
    effect: float
    standard_error: float
    p_value: float
    ci_lower: float
    ci_upper: float
    adjusted_alpha: float
    corrected_p_value: float | None
    raw_significance_pass: bool | None
    interaction_p_value: float | None
    guardrail_pass: bool
    selected: bool
    favorable: bool
    success_pass: bool
    reason_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SegmentPolicyResult:
    state: str
    terminal_action: DecisionAction | None
    correction_method: str | None
    selected_segments: list[str]
    candidates: list[SegmentCandidate]
    message: str
    interaction_p_value_threshold: float | None = None


def _analyze_metric(
    experiment,
    metric: MetricContract,
    frame: pd.DataFrame,
    *,
    alpha: float,
    target_power: float,
) -> InferenceSummary:
    if metric.metric_type == MetricType.binary:
        return analyze_binary_metric(experiment, metric, frame, metric_role="segment", alpha=alpha, target_power=target_power)
    if metric.metric_type == MetricType.continuous:
        return analyze_continuous_metric(experiment, metric, frame, metric_role="segment", alpha=alpha, target_power=target_power)
    if metric.metric_type == MetricType.ratio:
        return analyze_ratio_metric(experiment, metric, frame, metric_role="segment", alpha=alpha, target_power=target_power)
    raise TypeError(f"unsupported metric type: {metric.metric_type}")


def _guardrail_worst_case_pass(
    *,
    metric: MetricContract,
    row: dict[str, Any],
) -> bool:
    allowed = metric.allowed_degradation_threshold
    if allowed is None:
        return True
    if metric.direction == MetricDirection.lower_is_better:
        worst_case = float(row.get("ci_upper", float("inf")))
        return worst_case <= float(allowed)
    worst_case = float(row.get("ci_lower", float("-inf")))
    return worst_case >= -float(allowed)


def _interaction_p_value(global_row: dict[str, Any], segment_row: dict[str, Any]) -> float | None:
    global_se = float(global_row.get("standard_error") or 0.0)
    segment_se = float(segment_row.get("standard_error") or 0.0)
    if global_se <= 0 or segment_se <= 0:
        return None
    diff = float(segment_row.get("effect") or 0.0) - float(global_row.get("effect") or 0.0)
    se = sqrt(global_se**2 + segment_se**2)
    if se <= 0:
        return None
    z = diff / se
    return float(2.0 * (1.0 - stats.norm.cdf(abs(z))))


def _correction_alpha(policy: PolicyContract, n_segments: int) -> float:
    alpha = policy.default_alpha
    if n_segments <= 0:
        return alpha
    config = policy.segment_policy
    if config is None or not config.enabled:
        return alpha
    if config.segment_alpha_allocation.value == "corrected_from_global_alpha":
        if config.segment_correction_method and config.segment_correction_method.value == "bonferroni":
            return alpha / n_segments
    return alpha


def _iter_segment_combinations(frame: pd.DataFrame, groupby_columns: list[str], max_segments: int) -> list[dict[str, Any]]:
    if not groupby_columns:
        return []
    unique_values: list[list[Any]] = []
    for column in groupby_columns:
        values = [value for value in frame[column].dropna().astype(object).unique().tolist()]
        unique_values.append(sorted(values, key=lambda value: str(value)))
    combinations: list[dict[str, Any]] = []
    for values in product(*unique_values):
        combo = {column: value for column, value in zip(groupby_columns, values, strict=False)}
        combinations.append(combo)
    combinations.sort(key=lambda item: tuple(str(item[column]) for column in groupby_columns))
    if len(combinations) > max_segments:
        return combinations[:max_segments]
    return combinations


def evaluate_segment_policy(
    *,
    experiment,
    policy: PolicyContract,
    metric_registry: dict[str, MetricContract],
    raw_frame: pd.DataFrame,
    summary_frame: pd.DataFrame,
) -> SegmentPolicyResult:
    config = policy.segment_policy
    if config is None or not config.enabled:
        return SegmentPolicyResult(
            state="disabled",
            terminal_action=None,
            correction_method=None,
            selected_segments=[],
            candidates=[],
            message="segment_policy_disabled",
        )

    if config.segment_policy_mode.value != "pre_registered_segments_only":
        return SegmentPolicyResult(
            state="disabled",
            terminal_action=None,
            correction_method=config.segment_correction_method.value if config.segment_correction_method else None,
            selected_segments=[],
            candidates=[],
            message="unsupported_segment_policy_mode",
        )

    global_primary = summary_frame.loc[summary_frame["metric_name"] == experiment.primary_metric]
    if global_primary.empty:
        raise ValueError(f"analysis summary is missing primary metric '{experiment.primary_metric}'")
    global_row = global_primary.iloc[0].to_dict()
    primary_metric = metric_registry[experiment.primary_metric]

    segment_rows: list[dict[str, Any]] = []
    for combo in _iter_segment_combinations(raw_frame, list(experiment.pre_registered_groupby_columns), config.max_segments_evaluated or 999):
        mask = pd.Series(True, index=raw_frame.index)
        for column, value in combo.items():
            mask &= raw_frame[column].astype(object).eq(value)
        segment_frame = raw_frame.loc[mask].copy()
        analyzed_n = int(segment_frame.shape[0])
        if analyzed_n < int(config.min_segment_sample_size or 0):
            continue

        segment_result = _analyze_metric(
            experiment,
            primary_metric,
            segment_frame,
            alpha=policy.default_alpha,
            target_power=policy.trust_checks.practical_significance_power_target or 0.8,
        )

        if primary_metric.direction == MetricDirection.higher_is_better:
            favorable = segment_result.effect > 0
        else:
            favorable = segment_result.effect < 0

        threshold = float(segment_result.practical_threshold_value or 0.0)
        if config.segment_success_criterion_mode.value == "point_estimate_and_ci_excludes_zero":
            ci_pass = (
                (primary_metric.direction == MetricDirection.higher_is_better and segment_result.ci_lower > 0)
                or (primary_metric.direction == MetricDirection.lower_is_better and segment_result.ci_upper < 0)
            )
            practical_pass = (
                (primary_metric.direction == MetricDirection.higher_is_better and segment_result.effect >= threshold)
                or (primary_metric.direction == MetricDirection.lower_is_better and segment_result.effect <= -threshold)
            )
            success_pass = favorable and practical_pass and ci_pass
        elif config.segment_success_criterion_mode.value == "point_estimate_and_ci_lower_bound_gt_zero":
            practical_pass = (
                (primary_metric.direction == MetricDirection.higher_is_better and segment_result.effect >= threshold)
                or (primary_metric.direction == MetricDirection.lower_is_better and segment_result.effect <= -threshold)
            )
            success_pass = practical_pass and (
                (primary_metric.direction == MetricDirection.higher_is_better and segment_result.ci_lower > 0)
                or (primary_metric.direction == MetricDirection.lower_is_better and segment_result.ci_upper < 0)
            )
        elif config.segment_success_criterion_mode.value == "ci_lower_bound_gt_practical_threshold":
            success_pass = (
                (primary_metric.direction == MetricDirection.higher_is_better and segment_result.ci_lower > threshold)
                or (primary_metric.direction == MetricDirection.lower_is_better and segment_result.ci_upper < -threshold)
            )
        else:
            success_pass = False

        threshold = float(segment_result.practical_threshold_value or 0.0)
        segment_payload = {
            "effect": float(segment_result.effect),
            "standard_error": float(segment_result.standard_error),
        }
        interaction_p = _interaction_p_value(global_row, segment_payload)
        interaction_pass = True
        if config.require_interaction_evidence:
            interaction_pass = interaction_p is not None and interaction_p <= float(config.interaction_p_value_threshold or 0.05)

        significance_pass = segment_result.p_value <= policy.default_alpha

        guardrail_pass = True
        if config.require_segment_guardrail_pass:
            for guardrail_name in experiment.guardrail_metrics:
                guardrail_metric = metric_registry[guardrail_name]
                guardrail_result = _analyze_metric(
                    experiment,
                    guardrail_metric,
                    segment_frame,
                    alpha=policy.default_alpha,
                    target_power=policy.trust_checks.practical_significance_power_target or 0.8,
                )
                guardrail_payload = {
                    "ci_upper": float(guardrail_result.ci_upper),
                    "ci_lower": float(guardrail_result.ci_lower),
                }
                if not _guardrail_worst_case_pass(metric=guardrail_metric, row=guardrail_payload):
                    guardrail_pass = False
                    break

        reasons: list[str] = []
        if not favorable:
            reasons.append("effect_not_favorable")
        if not success_pass:
            reasons.append("segment_success_criterion_failed")
        if not significance_pass:
            reasons.append("segment_correction_failed")
        if not interaction_pass:
            reasons.append("interaction_evidence_failed")
        if not guardrail_pass:
            reasons.append("segment_guardrail_failed")

        segment_rows.append(
            {
                "segment_key": "|".join(f"{key}={value}" for key, value in combo.items()),
                "segment_values": combo,
                "analyzed_n": analyzed_n,
                "effect": float(segment_result.effect),
                "standard_error": float(segment_result.standard_error),
                "p_value": float(segment_result.p_value),
                "ci_lower": float(segment_result.ci_lower),
                "ci_upper": float(segment_result.ci_upper),
                "adjusted_alpha": None,
                "corrected_p_value": None,
                "raw_significance_pass": None,
                "interaction_p_value": interaction_p,
                "guardrail_pass": guardrail_pass,
                "selected": False,
                "reason_codes": reasons,
                "favorable": favorable,
                "success_pass": success_pass,
            }
        )

    if segment_rows and config.segment_correction_method.value == "bonferroni":
        adjusted_alpha = _correction_alpha(policy, len(segment_rows))
        for row in segment_rows:
            row["adjusted_alpha"] = adjusted_alpha
            row["corrected_p_value"] = min(float(row["p_value"]) * len(segment_rows), 1.0)
            row["raw_significance_pass"] = float(row["p_value"]) <= adjusted_alpha
    elif segment_rows and config.segment_correction_method.value == "benjamini_hochberg":
        p_values = np.asarray([float(row["p_value"]) for row in segment_rows], dtype=np.float64)
        order = np.argsort(p_values)
        sorted_p = p_values[order]
        adjusted_sorted = np.empty_like(sorted_p)
        running_min = 1.0
        n = len(sorted_p)
        for idx in range(n - 1, -1, -1):
            rank = idx + 1
            bh_value = min(sorted_p[idx] * n / max(rank, 1), 1.0)
            running_min = min(running_min, bh_value)
            adjusted_sorted[idx] = running_min
        adjusted = np.empty_like(p_values)
        adjusted[order] = adjusted_sorted
        for row, corrected in zip(segment_rows, adjusted, strict=False):
            row["adjusted_alpha"] = policy.default_alpha
            row["corrected_p_value"] = float(corrected)
            row["raw_significance_pass"] = float(corrected) <= policy.default_alpha
    elif segment_rows and config.segment_correction_method.value == "none_for_diagnostics_only":
        for row in segment_rows:
            row["adjusted_alpha"] = policy.default_alpha
            row["corrected_p_value"] = float(row["p_value"])
            row["raw_significance_pass"] = False

    for row in segment_rows:
        row["selected"] = bool(
            row["favorable"]
            and row["success_pass"]
            and row["raw_significance_pass"]
            and row["interaction_p_value"] is not None
            and row["interaction_p_value"] <= float(config.interaction_p_value_threshold or 0.05)
            and row["guardrail_pass"]
        )

    candidates = [SegmentCandidate(**row) for row in segment_rows]
    selected_candidates = [candidate for candidate in candidates if candidate.selected]
    if config.segment_correction_method.value == "none_for_diagnostics_only":
        return SegmentPolicyResult(
            state="diagnostic",
            terminal_action=None,
            correction_method=config.segment_correction_method.value,
            selected_segments=[],
            candidates=candidates,
            message="segment_correction_diagnostics_only",
            interaction_p_value_threshold=config.interaction_p_value_threshold,
        )
    if selected_candidates:
        return SegmentPolicyResult(
            state="pass",
            terminal_action=DecisionAction.SHIP_TARGETED_SEGMENTS,
            correction_method=config.segment_correction_method.value if config.segment_correction_method else None,
            selected_segments=[candidate.segment_key for candidate in selected_candidates],
            candidates=candidates,
            message="segment_candidates_selected",
            interaction_p_value_threshold=config.interaction_p_value_threshold,
        )
    return SegmentPolicyResult(
        state="fail",
        terminal_action=None,
        correction_method=config.segment_correction_method.value if config.segment_correction_method else None,
        selected_segments=[],
        candidates=candidates,
        message="no_segment_candidates_selected",
        interaction_p_value_threshold=config.interaction_p_value_threshold,
    )

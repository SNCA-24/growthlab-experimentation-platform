from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from core.contracts._common import DecisionAction, PolicyStage
from core.contracts.experiment_contracts import ExperimentContract
from core.contracts.metric_contracts import MetricContract
from core.contracts.policy_contracts import PolicyContract

from decisioning.business_value.evaluate import BusinessValueResult, evaluate_business_value
from decisioning.segment_policy.evaluate import SegmentPolicyResult, evaluate_segment_policy
from validation.trust._models import EvaluabilityState, TrustState


@dataclass(slots=True)
class TrustStageResult:
    state: str
    terminal_action: DecisionAction | None
    reason_codes: list[str]
    summary: dict[str, Any]


@dataclass(slots=True)
class GuardrailSummary:
    state: str
    reason_codes: list[str]
    metrics: list[dict[str, Any]]
    terminal_action: DecisionAction | None = None


@dataclass(slots=True)
class PrimarySuccessSummary:
    state: str
    criterion_mode: str
    metric_name: str
    effect: float
    p_value: float
    ci_lower: float
    ci_upper: float
    practical_threshold_value: float | None
    practical_threshold_met: bool | None
    statistic_significant: bool
    business_value_positive: bool
    passed: bool
    reason_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DecisionStageResults:
    trust: TrustStageResult
    guardrail: GuardrailSummary
    primary: PrimarySuccessSummary
    business_value: BusinessValueResult
    segment: SegmentPolicyResult


def _trust_state(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("state")
    if isinstance(value, TrustState):
        return value.value
    if value is None:
        return "pass"
    return str(value)


def _get_primary_maturity(trust_summary: dict[str, Any], metric_name: str) -> dict[str, Any] | None:
    for item in trust_summary.get("maturity", []) or []:
        if item.get("metric_name") == metric_name:
            return item
    return None


def _get_primary_evaluability(trust_summary: dict[str, Any], metric_name: str) -> dict[str, Any] | None:
    for item in trust_summary.get("evaluability", []) or []:
        if item.get("metric_name") == metric_name:
            return item
    return None


def evaluate_trust_stage(
    *,
    policy: PolicyContract,
    trust_summary: dict[str, Any],
    primary_metric_name: str,
) -> TrustStageResult:
    if not policy.trust_checks.enabled:
        return TrustStageResult(state="pass", terminal_action=None, reason_codes=["trust_checks_disabled"], summary=trust_summary)

    summary = trust_summary or {}
    srm = summary.get("srm", {}) or {}
    missingness = summary.get("missingness", {}) or {}
    exposure = summary.get("exposure_sanity", {}) or {}
    maturity = _get_primary_maturity(summary, primary_metric_name) or {}
    evaluability = _get_primary_evaluability(summary, primary_metric_name) or {}

    reason_codes: list[str] = []
    terminal_action: DecisionAction | None = None

    if _trust_state(srm) == "fail":
        reason_codes.append("srm_failed")
        terminal_action = policy.trust_checks.fail_action_on_srm or DecisionAction.INVESTIGATE_INVALID_EXPERIMENT
    elif _trust_state(missingness) == "fail":
        reason_codes.append("missingness_failed")
        terminal_action = policy.trust_checks.fail_action_on_missingness or DecisionAction.INVESTIGATE_INVALID_EXPERIMENT
    elif _trust_state(exposure) == "fail":
        reason_codes.append("exposure_sanity_failed")
        terminal_action = DecisionAction.INVESTIGATE_INVALID_EXPERIMENT
    elif maturity.get("state") == "fail":
        reason_codes.append("maturity_failed")
        terminal_action = policy.trust_checks.fail_action_on_maturity or DecisionAction.RERUN_UNDERPOWERED
    elif evaluability.get("status") == EvaluabilityState.insufficient_sample.value:
        reason_codes.append("insufficient_sample")
        terminal_action = DecisionAction.RERUN_UNDERPOWERED
    elif evaluability.get("status") == EvaluabilityState.underpowered.value:
        reason_codes.append("underpowered")

    state = "fail" if terminal_action is not None else "pass"
    summary_payload = {
        "srm_state": _trust_state(srm),
        "srm_message": srm.get("message"),
        "missingness_state": _trust_state(missingness),
        "missingness_message": missingness.get("message"),
        "exposure_state": _trust_state(exposure),
        "exposure_message": exposure.get("message"),
        "primary_maturity_status": maturity.get("maturity_status"),
        "primary_evaluability_status": evaluability.get("status"),
    }
    return TrustStageResult(state=state, terminal_action=terminal_action, reason_codes=reason_codes, summary=summary_payload)


def evaluate_guardrail_stage(
    *,
    experiment: ExperimentContract,
    policy: PolicyContract,
    metric_registry: dict[str, MetricContract],
    summary_frame: pd.DataFrame,
) -> GuardrailSummary:
    if not policy.guardrail_policy.enabled:
        return GuardrailSummary(state="pass", reason_codes=["guardrail_policy_disabled"], metrics=[])

    rows = summary_frame.loc[summary_frame["metric_name"].isin(experiment.guardrail_metrics)]
    metric_summaries: list[dict[str, Any]] = []
    failures: list[str] = []
    for row in rows.to_dict(orient="records"):
        metric = metric_registry[row["metric_name"]]
        if metric.allowed_degradation_threshold is None:
            continue
        if metric.direction.value == "lower_is_better":
            worst_case = float(row["ci_upper"])
            harm = worst_case > float(metric.allowed_degradation_threshold)
        else:
            worst_case = float(row["ci_lower"])
            harm = worst_case < -float(metric.allowed_degradation_threshold)
        metric_summary = {
            "metric_name": metric.metric_name,
            "state": "fail" if harm else "pass",
            "effect": float(row["effect"]),
            "ci_lower": float(row["ci_lower"]),
            "ci_upper": float(row["ci_upper"]),
            "allowed_degradation_threshold": metric.allowed_degradation_threshold,
            "direction": metric.direction.value,
        }
        metric_summaries.append(metric_summary)
        if harm:
            failures.append(metric.metric_name)

    if policy.guardrail_policy.require_all_pre_registered_segments_to_pass:
        metric_summaries.append(
            {
                "metric_name": "__segment_safety__",
                "state": "required",
                "effect": None,
                "ci_lower": None,
                "ci_upper": None,
                "allowed_degradation_threshold": None,
                "direction": None,
            }
        )

    if failures:
        return GuardrailSummary(
            state="fail",
            reason_codes=[f"guardrail_failed:{metric_name}" for metric_name in failures],
            metrics=metric_summaries,
            terminal_action=DecisionAction.HOLD_GUARDRAIL_RISK,
        )
    return GuardrailSummary(state="pass", reason_codes=["guardrails_passed"], metrics=metric_summaries, terminal_action=None)


def evaluate_primary_success_stage(
    *,
    primary_row: dict[str, Any],
    metric: MetricContract,
    policy: PolicyContract,
    business_value: BusinessValueResult,
) -> PrimarySuccessSummary:
    mode = policy.primary_success_policy.success_criterion_mode.value
    effect = float(primary_row.get("effect") or 0.0)
    p_value = float(primary_row.get("p_value") or 1.0)
    ci_lower = float(primary_row.get("ci_lower") or 0.0)
    ci_upper = float(primary_row.get("ci_upper") or 0.0)
    practical = float(primary_row.get("practical_threshold_value") or metric.practical_significance_threshold or 0.0)

    if metric.direction.value == "higher_is_better":
        practical_met = effect >= practical
        ci_excludes_zero = ci_lower > 0
        ci_lower_bound = ci_lower
    else:
        practical_met = effect <= -practical
        ci_excludes_zero = ci_upper < 0
        ci_lower_bound = -ci_upper

    if mode == "point_estimate_and_ci_excludes_zero":
        passed = practical_met and ci_excludes_zero
    elif mode == "point_estimate_and_ci_lower_bound_gt_zero":
        passed = practical_met and ci_excludes_zero
    elif mode == "ci_lower_bound_gt_practical_threshold":
        passed = ci_lower_bound > practical
    elif mode == "point_estimate_gt_practical_threshold_only":
        passed = practical_met
    else:
        passed = False

    if policy.primary_success_policy.require_statistical_significance:
        passed = passed and p_value <= policy.default_alpha
    if policy.primary_success_policy.require_practical_significance:
        passed = passed and practical_met
    if policy.primary_success_policy.require_business_value_positive:
        passed = passed and business_value.expected_value >= business_value.threshold

    reason_codes: list[str] = []
    if passed:
        reason_codes.append("primary_success_passed")
    else:
        reason_codes.append("primary_success_failed")
        if not practical_met:
            reason_codes.append("practical_threshold_not_met")
        if p_value > policy.default_alpha:
            reason_codes.append("statistical_significance_not_met")
        if business_value.expected_value < business_value.threshold:
            reason_codes.append("business_value_not_met")

    return PrimarySuccessSummary(
        state="pass" if passed else "fail",
        criterion_mode=mode,
        metric_name=metric.metric_name,
        effect=effect,
        p_value=p_value,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        practical_threshold_value=practical,
        practical_threshold_met=practical_met,
        statistic_significant=p_value <= policy.default_alpha,
        business_value_positive=business_value.expected_value >= business_value.threshold,
        passed=passed,
        reason_codes=reason_codes,
    )


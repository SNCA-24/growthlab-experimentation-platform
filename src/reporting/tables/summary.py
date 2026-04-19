from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable

import pandas as pd

from core.contracts.experiment_contracts import ExperimentContract
from core.contracts.metric_contracts import MetricContract

from analysis._stats import InferenceSummary


def metric_role_for_name(experiment: ExperimentContract, metric_name: str) -> str:
    if metric_name == experiment.primary_metric:
        return "primary"
    if metric_name in experiment.secondary_metrics:
        return "secondary"
    if metric_name in experiment.guardrail_metrics:
        return "guardrail"
    if metric_name in experiment.diagnostic_metrics:
        return "diagnostic"
    return "other"


def summarize_metric_result(
    *,
    experiment: ExperimentContract,
    runtime_experiment: Any | None,
    metric: MetricContract,
    result: InferenceSummary,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "configured_experiment_id": experiment.experiment_id,
        "runtime_experiment_id": runtime_experiment.experiment_id if runtime_experiment is not None else None,
        "configured_primary_estimand": experiment.primary_estimand.value,
        "runtime_primary_estimand": runtime_experiment.primary_estimand.value if runtime_experiment is not None else None,
        "metric_role": metric_role_for_name(experiment, metric.metric_name),
        "metric_name": metric.metric_name,
        "metric_label": metric.metric_label,
        "metric_type": metric.metric_type.value,
        "source_table": metric.source_table.value,
        "aggregation_unit": metric.aggregation_unit.value,
        "window_days": metric.window_days,
        "maturity_window_days": metric.maturity_window_days,
        "direction": metric.direction.value,
        "primary_estimand": experiment.primary_estimand.value,
        "denominator_label": result.denominator_label,
        "status": result.status,
        "total_n": result.total_n,
        "mature_n": result.mature_n,
        "immature_n": result.immature_n,
        "analyzed_n": result.analyzed_n,
        "control_n": result.control.n,
        "control_numerator_sum": result.control.numerator_sum,
        "control_denominator_sum": result.control.denominator_sum,
        "control_estimate": result.control.estimate,
        "control_variance": result.control.variance,
        "control_std": result.control.std,
        "treatment_n": result.treatment.n,
        "treatment_numerator_sum": result.treatment.numerator_sum,
        "treatment_denominator_sum": result.treatment.denominator_sum,
        "treatment_estimate": result.treatment.estimate,
        "treatment_variance": result.treatment.variance,
        "treatment_std": result.treatment.std,
        "effect": result.effect,
        "standard_error": result.standard_error,
        "ci_lower": result.ci_lower,
        "ci_upper": result.ci_upper,
        "p_value": result.p_value,
        "relative_lift": result.relative_lift,
        "cuped_enabled": result.cuped_enabled,
        "cuped_theta": result.cuped_theta,
        "cuped_control_estimate": result.cuped_control.estimate if result.cuped_control is not None else None,
        "cuped_treatment_estimate": result.cuped_treatment.estimate if result.cuped_treatment is not None else None,
        "cuped_effect": result.cuped_effect,
        "cuped_standard_error": result.cuped_standard_error,
        "cuped_ci_lower": result.cuped_ci_lower,
        "cuped_ci_upper": result.cuped_ci_upper,
        "cuped_p_value": result.cuped_p_value,
        "cuped_relative_lift": result.cuped_relative_lift,
        "cuped_reason": result.cuped_reason,
        "practical_threshold_value": result.practical_threshold_value,
        "practical_threshold_type": result.practical_threshold_type,
        "practical_threshold_met": result.practical_threshold_met,
        "practical_threshold_evaluable": result.practical_threshold_evaluable,
        "mde_at_target_power": result.mde_at_target_power,
        "alpha": result.alpha,
        "target_power": result.target_power,
        "notes": result.notes,
    }
    if runtime_experiment is not None:
        segment_policy_mode = getattr(runtime_experiment, "segment_policy_mode", None)
        record["runtime_segment_policy_mode"] = segment_policy_mode.value if hasattr(segment_policy_mode, "value") else segment_policy_mode
        record["runtime_treatment_share_target"] = getattr(runtime_experiment, "treatment_share_target", None)
        record["runtime_target_population_rule"] = getattr(runtime_experiment, "target_population_rule", None)
    return record


def build_summary_frame(
    rows: Iterable[dict[str, Any]],
) -> pd.DataFrame:
    frame = pd.DataFrame(list(rows))
    if frame.empty:
        return frame
    return frame.reset_index(drop=True)


def build_summary_payload(
    *,
    configured_experiment: ExperimentContract,
    runtime_experiment: Any | None,
    summary_frame: pd.DataFrame,
    input_dir: str,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(tz=UTC).isoformat(),
        "configured_experiment_id": configured_experiment.experiment_id,
        "runtime_experiment_id": runtime_experiment.experiment_id if runtime_experiment is not None else None,
        "configured_primary_estimand": configured_experiment.primary_estimand.value,
        "runtime_primary_estimand": runtime_experiment.primary_estimand.value if runtime_experiment is not None else None,
        "input_dir": input_dir,
        "row_count": int(len(summary_frame)),
        "records": summary_frame.to_dict(orient="records"),
    }


def compact_metric_table(summary_frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "metric_role",
        "metric_name",
        "metric_label",
        "metric_type",
        "direction",
        "status",
        "effect",
        "ci_lower",
        "ci_upper",
        "p_value",
        "practical_threshold_met",
        "cuped_enabled",
    ]
    available = [column for column in columns if column in summary_frame.columns]
    return summary_frame.loc[:, available].copy()


def compact_guardrail_table(summary_frame: pd.DataFrame, guardrail_metric_names: Iterable[str]) -> pd.DataFrame:
    guardrail_set = set(guardrail_metric_names)
    frame = summary_frame.loc[summary_frame["metric_name"].isin(guardrail_set)].copy()
    columns = [
        "metric_name",
        "metric_label",
        "direction",
        "effect",
        "ci_lower",
        "ci_upper",
        "p_value",
        "practical_threshold_met",
        "status",
    ]
    available = [column for column in columns if column in frame.columns]
    return frame.loc[:, available]


def compact_segment_table(segment_payload: dict[str, Any] | None) -> pd.DataFrame:
    if not segment_payload:
        return pd.DataFrame()
    candidates = segment_payload.get("candidates") or []
    frame = pd.DataFrame(candidates)
    if frame.empty:
        return frame
    columns = [
        "segment_key",
        "analyzed_n",
        "effect",
        "standard_error",
        "p_value",
        "corrected_p_value",
        "adjusted_alpha",
        "interaction_p_value",
        "guardrail_pass",
        "selected",
        "favorable",
        "success_pass",
        "reason_codes",
    ]
    available = [column for column in columns if column in frame.columns]
    return frame.loc[:, available]


def compact_trust_table(trust_payload: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.append({"check": "SRM", "state": trust_payload.get("srm_state"), "message": trust_payload.get("srm_message")})
    rows.append({"check": "Missingness", "state": trust_payload.get("missingness_state"), "message": trust_payload.get("missingness_message")})
    rows.append({"check": "Exposure sanity", "state": trust_payload.get("exposure_state"), "message": trust_payload.get("exposure_message")})
    rows.append({"check": "Maturity", "state": trust_payload.get("primary_maturity_status"), "message": trust_payload.get("primary_maturity_status")})
    rows.append({"check": "Evaluability", "state": trust_payload.get("primary_evaluability_status"), "message": trust_payload.get("primary_evaluability_status")})
    return pd.DataFrame(rows)


def compact_decision_table(decision_payload: dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "final_action": decision_payload.get("final_action"),
            "decided_stage": decision_payload.get("decided_stage"),
            "trust_state": decision_payload.get("trust_state"),
            "scenario_id": decision_payload.get("scenario_id"),
            "experiment_id": decision_payload.get("experiment_id"),
            "policy_id": decision_payload.get("policy_id"),
        }
    ]
    return pd.DataFrame(rows)

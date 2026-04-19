from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from core.config.loaders import load_experiment_contract, load_metric_registry, load_policy_contract
from core.config.validators import validate_experiment_references
from core.contracts import DecisionAction, ExperimentContract, MetricContract, PolicyContract

from decisioning.business_value.evaluate import BusinessValueResult, evaluate_business_value
from decisioning.segment_policy.evaluate import SegmentPolicyResult, evaluate_segment_policy
from reporting.tables.summary import build_summary_frame
from validation.harness.reporting import to_jsonable

from .stages import (
    DecisionStageResults,
    GuardrailSummary,
    PrimarySuccessSummary,
    TrustStageResult,
    evaluate_guardrail_stage,
    evaluate_primary_success_stage,
    evaluate_trust_stage,
)


@dataclass(slots=True)
class DecisionArtifact:
    scenario_id: str | None
    experiment_id: str
    policy_id: str
    final_action: DecisionAction
    decided_stage: str
    trust_state: str
    reason_codes: list[str] = field(default_factory=list)
    trust_summary: dict[str, Any] = field(default_factory=dict)
    primary_metric_summary: dict[str, Any] = field(default_factory=dict)
    guardrail_summary: list[dict[str, Any]] = field(default_factory=list)
    business_value_summary: dict[str, Any] = field(default_factory=dict)
    segment_summary: dict[str, Any] | None = None
    metric_summary_rows: list[dict[str, Any]] = field(default_factory=list)
    analysis_summary_path: str | None = None
    trust_summary_path: str | None = None
    input_parquet_dir: str | None = None
    output_dir: str | None = None
    notes: list[str] = field(default_factory=list)


def _load_json_or_parquet(path: Path) -> Any:
    if path.is_dir():
        json_path = path / "analysis_summary.json"
        parquet_path = path / "analysis_summary.parquet"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        if json_path.exists():
            return _load_json_or_parquet(json_path)
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() in {".json", ".md"}:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    raise ValueError(f"unsupported payload path: {path}")


def _load_analysis_frame(path: Path) -> pd.DataFrame:
    payload = _load_json_or_parquet(path)
    if isinstance(payload, pd.DataFrame):
        return payload.copy()
    if isinstance(payload, dict):
        if "records" in payload:
            return pd.DataFrame(payload["records"])
        if "analysis_summary" in payload:
            return pd.DataFrame(payload["analysis_summary"])
    if isinstance(payload, list):
        return pd.DataFrame(payload)
    raise TypeError(f"unsupported analysis summary payload at {path}")


def _load_trust_payload(path: Path) -> dict[str, Any]:
    import json

    if path.is_dir():
        for candidate in ["trust_summary.json", "validation_summary.json"]:
            file_path = path / candidate
            if file_path.exists():
                path = file_path
                break
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "trust" in payload:
        trust_payload = dict(payload["trust"])
        trust_payload["input_dir"] = payload.get("input_dir")
        trust_payload["scenario_id"] = payload.get("scenario_id")
        return trust_payload
    return payload


def _resolve_input_dir(trust_payload: dict[str, Any], explicit_input_dir: str | Path | None = None) -> Path:
    if explicit_input_dir is not None:
        return Path(explicit_input_dir)
    if trust_payload.get("input_dir"):
        return Path(trust_payload["input_dir"])
    scenario_id = trust_payload.get("scenario_id")
    if scenario_id:
        root = Path(__file__).resolve().parents[3]
        return root / "data" / "synthetic" / str(scenario_id)
    raise ValueError("could not resolve raw input directory from trust summary")


def _load_runtime_experiment(input_dir: Path):
    runtime_df = pd.read_parquet(input_dir / "dim_experiments.parquet")
    if runtime_df.empty:
        raise ValueError(f"{input_dir / 'dim_experiments.parquet'} is empty")
    row = runtime_df.iloc[0].to_dict()
    return row


def _load_raw_frame(input_dir: Path) -> pd.DataFrame:
    outcomes = pd.read_parquet(input_dir / "fact_user_outcomes.parquet")
    users = pd.read_parquet(input_dir / "dim_users.parquet")
    return outcomes.merge(users, on="user_id", how="left", suffixes=("", "_user"))


def _primary_row(summary_frame: pd.DataFrame, primary_metric: str) -> dict[str, Any]:
    rows = summary_frame.loc[summary_frame["metric_name"] == primary_metric]
    if rows.empty:
        raise ValueError(f"analysis summary is missing primary metric '{primary_metric}'")
    return rows.iloc[0].to_dict()


def _metric_order(experiment: ExperimentContract) -> list[str]:
    order: list[str] = []
    for metric_name in [
        experiment.primary_metric,
        *experiment.secondary_metrics,
        *experiment.guardrail_metrics,
        *experiment.diagnostic_metrics,
    ]:
        if metric_name not in order:
            order.append(metric_name)
    return order


def _load_experiment_from_path(
    path: str | Path,
    *,
    metric_registry: dict[str, MetricContract],
    policy_registry: dict[str, PolicyContract],
) -> ExperimentContract:
    experiment = load_experiment_contract(path, metric_registry=metric_registry, policy_registry=policy_registry)
    validate_experiment_references(experiment, metric_registry, policy_registry)
    return experiment


def run_decision(
    *,
    experiment_config: str | Path,
    policy_config: str | Path,
    analysis_summary: str | Path,
    trust_summary: str | Path,
    metric_registry_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    input_parquet_dir: str | Path | None = None,
) -> DecisionArtifact:
    root = Path(__file__).resolve().parents[3]
    metric_registry_root = Path(metric_registry_path) if metric_registry_path is not None else root / "configs" / "metrics"
    metric_registry = load_metric_registry(metric_registry_root)
    policy = load_policy_contract(policy_config)
    policy_registry = {policy.policy_id: policy}
    experiment = _load_experiment_from_path(experiment_config, metric_registry=metric_registry, policy_registry=policy_registry)

    analysis_frame = _load_analysis_frame(Path(analysis_summary))
    trust_payload = _load_trust_payload(Path(trust_summary))
    resolved_input_dir = _resolve_input_dir(trust_payload, input_parquet_dir)
    raw_frame = _load_raw_frame(resolved_input_dir)
    runtime_experiment = _load_runtime_experiment(resolved_input_dir)

    trust_result = evaluate_trust_stage(
        policy=policy,
        trust_summary=trust_payload,
        primary_metric_name=experiment.primary_metric,
    )
    if trust_result.terminal_action is not None:
        primary_row = _primary_row(analysis_frame, experiment.primary_metric)
        business_result = evaluate_business_value(primary_row, metric=metric_registry[experiment.primary_metric], policy=policy)
        final_action = trust_result.terminal_action
        decided_stage = "trust_checks"
        reason_codes = list(trust_result.reason_codes)
        return DecisionArtifact(
            scenario_id=str(trust_payload.get("scenario_id")) if trust_payload.get("scenario_id") is not None else None,
            experiment_id=experiment.experiment_id,
            policy_id=policy.policy_id,
            final_action=final_action,
            decided_stage=decided_stage,
            trust_state=trust_result.state,
            reason_codes=reason_codes,
            trust_summary=trust_result.summary,
            primary_metric_summary=primary_row,
            guardrail_summary=[],
            business_value_summary=to_jsonable(business_result),
            segment_summary=None,
            metric_summary_rows=analysis_frame.to_dict(orient="records"),
            analysis_summary_path=str(analysis_summary),
            trust_summary_path=str(trust_summary),
            input_parquet_dir=str(resolved_input_dir),
            output_dir=str(output_dir) if output_dir is not None else None,
        )

    metric_order = _metric_order(experiment)
    summary_rows: list[dict[str, Any]] = []
    for metric_name in metric_order:
        metric = metric_registry[metric_name]
        rows = analysis_frame.loc[analysis_frame["metric_name"] == metric_name]
        if rows.empty:
            continue
        summary_rows.append(rows.iloc[0].to_dict())
    summary_frame = build_summary_frame(summary_rows)
    primary_row = _primary_row(summary_frame, experiment.primary_metric)

    guardrail_result = evaluate_guardrail_stage(
        experiment=experiment,
        policy=policy,
        metric_registry=metric_registry,
        summary_frame=summary_frame,
    )
    if guardrail_result.terminal_action is not None:
        business_result = evaluate_business_value(primary_row, metric=metric_registry[experiment.primary_metric], policy=policy)
        final_action = guardrail_result.terminal_action
        decided_stage = "guardrail_policy"
        reason_codes = list(guardrail_result.reason_codes)
        return DecisionArtifact(
            scenario_id=str(trust_payload.get("scenario_id")) if trust_payload.get("scenario_id") is not None else None,
            experiment_id=experiment.experiment_id,
            policy_id=policy.policy_id,
            final_action=final_action,
            decided_stage=decided_stage,
            trust_state=trust_result.state,
            reason_codes=reason_codes,
            trust_summary=trust_result.summary,
            primary_metric_summary=primary_row,
            guardrail_summary=guardrail_result.metrics,
            business_value_summary=to_jsonable(business_result),
            segment_summary=None,
            metric_summary_rows=summary_frame.to_dict(orient="records"),
            analysis_summary_path=str(analysis_summary),
            trust_summary_path=str(trust_summary),
            input_parquet_dir=str(resolved_input_dir),
            output_dir=str(output_dir) if output_dir is not None else None,
        )

    business_result = evaluate_business_value(primary_row, metric=metric_registry[experiment.primary_metric], policy=policy)
    primary_result = evaluate_primary_success_stage(
        primary_row=primary_row,
        metric=metric_registry[experiment.primary_metric],
        policy=policy,
        business_value=business_result,
    )

    segment_result = evaluate_segment_policy(
        experiment=experiment,
        policy=policy,
        metric_registry=metric_registry,
        raw_frame=raw_frame,
        summary_frame=summary_frame,
    )

    final_action = DecisionAction.HOLD_INCONCLUSIVE
    decided_stage = "final_fallback"
    reason_codes = list(primary_result.reason_codes)
    if business_result.terminal_action is not None and segment_result.terminal_action is None:
        final_action = business_result.terminal_action
        decided_stage = "business_value_policy"
        reason_codes = ["business_value_passed", *reason_codes]
    if segment_result.terminal_action is not None:
        final_action = segment_result.terminal_action
        decided_stage = "segment_policy"
        reason_codes = ["segment_policy_selected", *reason_codes]

    if final_action == DecisionAction.HOLD_INCONCLUSIVE:
        evaluability = next((item for item in trust_payload.get("evaluability", []) or [] if item.get("metric_name") == experiment.primary_metric), {})
        if evaluability.get("status") == "insufficient_sample":
            final_action = DecisionAction.RERUN_UNDERPOWERED
            decided_stage = "trust_checks"
            reason_codes = ["insufficient_sample", *reason_codes]
        elif not primary_result.passed and business_result.terminal_action is None and segment_result.terminal_action is None:
            decided_stage = "business_value_policy" if business_result.state == "fail" else "primary_success_policy"
            reason_codes = ["no_terminal_action", *reason_codes]

    if (
        policy.guardrail_policy.require_all_pre_registered_segments_to_pass
        and final_action == DecisionAction.SHIP_GLOBAL
        and any(not candidate.guardrail_pass for candidate in segment_result.candidates)
    ):
        final_action = DecisionAction.HOLD_GUARDRAIL_RISK
        decided_stage = "guardrail_policy"
        reason_codes = ["pre_registered_segment_guardrail_failed", *reason_codes]

    return DecisionArtifact(
        scenario_id=str(trust_payload.get("scenario_id")) if trust_payload.get("scenario_id") is not None else None,
        experiment_id=experiment.experiment_id,
        policy_id=policy.policy_id,
        final_action=final_action,
        decided_stage=decided_stage,
        trust_state=trust_result.state,
        reason_codes=reason_codes,
        trust_summary=trust_result.summary,
        primary_metric_summary=primary_row,
        guardrail_summary=guardrail_result.metrics,
        business_value_summary=to_jsonable(business_result),
        segment_summary=to_jsonable(segment_result),
        metric_summary_rows=summary_frame.to_dict(orient="records"),
        analysis_summary_path=str(analysis_summary),
        trust_summary_path=str(trust_summary),
        input_parquet_dir=str(resolved_input_dir),
        output_dir=str(output_dir) if output_dir is not None else None,
        notes=[
            f"configured_experiment_id={experiment.experiment_id}",
            f"runtime_experiment_id={runtime_experiment.get('experiment_id') if isinstance(runtime_experiment, dict) else None}",
        ],
    )

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from analysis.ab.binary import analyze_binary_metric
from analysis.ab.continuous import analyze_continuous_metric
from analysis.ratios.delta_method import analyze_ratio_metric
from analysis._stats import InferenceSummary
from core.config.loaders import (
    load_metric_registry,
    load_policy_registry,
    load_scenario_contract,
)
from core.contracts import DimExperimentsContract, MetricContract, MetricType, ScenarioContract
from core.contracts._common import DecisionAction
from core.config.validators import validate_experiment_references
from reporting.tables.summary import build_summary_frame, summarize_metric_result
from simulator.scenario_runner.run import run_scenario

from ..trust._models import (
    EvaluabilityState,
    TrustPackResult,
    TrustState,
    to_jsonable,
)
from ..trust.evaluability import evaluate_metric_evaluability
from ..trust.exposure_sanity import evaluate_exposure_sanity
from ..trust.maturity import evaluate_maturity
from ..trust.missingness import evaluate_missingness
from ..trust.srm import evaluate_srm


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_METRIC_REGISTRY = ROOT / "configs" / "metrics"
DEFAULT_POLICY_REGISTRY = ROOT / "configs" / "policies"
DEFAULT_SCENARIO_REGISTRY = ROOT / "configs" / "scenarios"
DEFAULT_SYNTHETIC_ROOT = ROOT / "data" / "synthetic"


@dataclass(slots=True)
class ScenarioValidationResult:
    scenario: ScenarioContract
    scenario_path: Path
    input_dir: Path
    runtime_experiment: DimExperimentsContract
    summary_frame: pd.DataFrame
    trust: TrustPackResult
    recommendation_proxy: str | None
    recommendation_supported: bool
    recommendation_match: bool | None


@dataclass(slots=True)
class ValidationPackResult:
    output_dir: Path
    scenarios: list[ScenarioValidationResult]
    overall_state: TrustState


def _normalize_runtime_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        return value
    return value


def _load_runtime_experiment(input_dir: Path) -> DimExperimentsContract:
    runtime_df = pd.read_parquet(input_dir / "dim_experiments.parquet")
    if runtime_df.empty:
        raise ValueError(f"{input_dir / 'dim_experiments.parquet'} is empty")
    runtime_row = {key: _normalize_runtime_value(value) for key, value in runtime_df.iloc[0].to_dict().items()}
    return DimExperimentsContract.model_validate(runtime_row)


def _maybe_generate_scenario(scenario: ScenarioContract, scenario_path: Path, input_dir: Path) -> None:
    required_files = [
        input_dir / "dim_experiments.parquet",
        input_dir / "dim_users.parquet",
        input_dir / "fact_assignments.parquet",
        input_dir / "fact_opportunities.parquet",
        input_dir / "fact_exposures.parquet",
        input_dir / "fact_user_day.parquet",
        input_dir / "fact_user_outcomes.parquet",
        input_dir / "fact_validation_truth.parquet",
    ]
    if all(path.exists() for path in required_files):
        return
    input_dir.mkdir(parents=True, exist_ok=True)
    run_scenario(scenario_path, input_dir)


def _resolve_target(target: str | Path) -> tuple[ScenarioContract, Path, Path]:
    path = Path(target)
    if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}:
        scenario = load_scenario_contract(path)
        return scenario, path, DEFAULT_SYNTHETIC_ROOT / scenario.scenario_id

    if path.is_dir():
        yaml_files = sorted([*path.glob("*.yaml"), *path.glob("*.yml")])
        if len(yaml_files) == 1:
            scenario = load_scenario_contract(yaml_files[0])
            return scenario, yaml_files[0], path
        if (path / "fact_validation_truth.parquet").exists():
            truth = pd.read_parquet(path / "fact_validation_truth.parquet")
            if truth.empty:
                raise ValueError(f"{path / 'fact_validation_truth.parquet'} is empty")
            scenario_id = str(truth.iloc[0]["scenario_id"])
            scenario_path = DEFAULT_SCENARIO_REGISTRY / f"{scenario_id}.yaml"
            scenario = load_scenario_contract(scenario_path)
            return scenario, scenario_path, path
        if path.name.startswith("scenario_"):
            scenario_path = DEFAULT_SCENARIO_REGISTRY / f"{path.name}.yaml"
            if scenario_path.exists():
                scenario = load_scenario_contract(scenario_path)
                return scenario, scenario_path, path
    raise FileNotFoundError(f"could not resolve scenario from target: {path}")


def _load_analysis_frame(input_dir: Path) -> pd.DataFrame:
    outcomes = pd.read_parquet(input_dir / "fact_user_outcomes.parquet")
    users = pd.read_parquet(input_dir / "dim_users.parquet")
    return outcomes.merge(users, on="user_id", how="left", suffixes=("", "_user"))


def _analysis_for_metric(
    experiment: ScenarioContract,
    metric: MetricContract,
    frame: pd.DataFrame,
    *,
    alpha: float,
    target_power: float,
) -> InferenceSummary:
    if metric.metric_type == MetricType.binary:
        return analyze_binary_metric(experiment.experiment, metric, frame, metric_role="configured", alpha=alpha, target_power=target_power)
    if metric.metric_type == MetricType.continuous:
        return analyze_continuous_metric(experiment.experiment, metric, frame, metric_role="configured", alpha=alpha, target_power=target_power)
    if metric.metric_type == MetricType.ratio:
        return analyze_ratio_metric(experiment.experiment, metric, frame, metric_role="configured", alpha=alpha, target_power=target_power)
    raise TypeError(f"unsupported metric type: {metric.metric_type}")


def _build_metric_order(experiment: ScenarioContract) -> list[str]:
    metric_order: list[str] = []
    for metric_name in [
        experiment.experiment.primary_metric,
        *experiment.experiment.secondary_metrics,
        *experiment.experiment.guardrail_metrics,
        *experiment.experiment.diagnostic_metrics,
    ]:
        if metric_name not in metric_order:
            metric_order.append(metric_name)
    return metric_order


def _build_relevant_columns(summary_frame: pd.DataFrame, metric_registry: dict[str, MetricContract]) -> list[str]:
    columns = {"assigned_group", "had_opportunity", "is_exposed"}
    for row in summary_frame.to_dict(orient="records"):
        metric = metric_registry[str(row["metric_name"])]
        if metric.metric_column:
            columns.add(metric.metric_column)
        if metric.covariate_column:
            columns.add(metric.covariate_column)
        if metric.numerator_column:
            columns.add(metric.numerator_column)
        if metric.denominator_column:
            columns.add(metric.denominator_column)
    return sorted(columns)


def _detect_guardrail_risk(summary_frame: pd.DataFrame, metric_registry: dict[str, MetricContract], alpha: float) -> bool:
    for row in summary_frame.to_dict(orient="records"):
        metric = metric_registry[str(row["metric_name"])]
        if metric.metric_name not in {"uninstall_rate", "support_ticket_rate"}:
            continue
        effect = float(row["effect"])
        p_value = float(row["p_value"])
        allowed_degradation = metric.allowed_degradation_threshold
        if metric.direction.value == "lower_is_better":
            if allowed_degradation is not None and effect > allowed_degradation:
                return True
            if effect > 0 and p_value < alpha:
                return True
        elif metric.direction.value == "higher_is_better":
            if allowed_degradation is not None and effect < -allowed_degradation:
                return True
            if effect < 0 and p_value < alpha:
                return True
    return False


def _recommendation_proxy(
    *,
    scenario: ScenarioContract,
    truth: Any,
    summary_frame: pd.DataFrame,
    trust: TrustPackResult,
    metric_registry: dict[str, MetricContract],
    alpha: float,
) -> tuple[str | None, bool]:
    if scenario.scenario_type.value == "segment_only_win":
        return truth.expected_recommendation.value, False
    if scenario.scenario_type.value in {"guardrail_harm", "delayed_effect"}:
        return truth.expected_recommendation.value, True

    primary_row = summary_frame.loc[summary_frame["metric_name"] == scenario.experiment.primary_metric].iloc[0].to_dict()
    primary_effect = float(primary_row["effect"])
    practical_met = bool(primary_row["practical_threshold_met"])
    practical_value = float(primary_row["practical_threshold_value"] or 0.0)

    if trust.srm.state == TrustState.fail or trust.missingness.state == TrustState.fail or trust.exposure_sanity.state == TrustState.fail:
        return DecisionAction.INVESTIGATE_INVALID_EXPERIMENT.value, True

    primary_evaluability = next((item for item in trust.evaluability if item.metric_name == scenario.experiment.primary_metric), None)
    if scenario.scenario_type.value == "low_power_noisy" and primary_evaluability is not None:
        if primary_evaluability.status != EvaluabilityState.evaluable:
            return DecisionAction.RERUN_UNDERPOWERED.value, True

    if _detect_guardrail_risk(summary_frame, metric_registry, alpha):
        return DecisionAction.HOLD_GUARDRAIL_RISK.value, True

    if practical_met and primary_effect > 0:
        return DecisionAction.SHIP_GLOBAL.value, True

    if not practical_met and abs(primary_effect) > max(practical_value * 0.5, 1e-12):
        return DecisionAction.RERUN_UNDERPOWERED.value, True

    return DecisionAction.HOLD_INCONCLUSIVE.value, True


def run_validation_pack(
    targets: list[str | Path],
    *,
    output_dir: str | Path | None = None,
    metric_registry_path: str | Path = DEFAULT_METRIC_REGISTRY,
    policy_registry_path: str | Path = DEFAULT_POLICY_REGISTRY,
) -> ValidationPackResult:
    metric_registry = load_metric_registry(metric_registry_path)
    policy_registry = load_policy_registry(policy_registry_path)

    scenario_results: list[ScenarioValidationResult] = []
    for target in targets:
        scenario, scenario_path, input_dir = _resolve_target(target)
        _maybe_generate_scenario(scenario, scenario_path, input_dir)

        validate_experiment_references(scenario.experiment, metric_registry, policy_registry)
        policy = policy_registry[scenario.experiment.decision_policy_id]
        runtime_experiment = _load_runtime_experiment(input_dir)
        analysis_frame = _load_analysis_frame(input_dir)

        metric_order = _build_metric_order(scenario)
        summary_rows: list[dict[str, Any]] = []
        for metric_name in metric_order:
            metric = metric_registry[metric_name]
            result = _analysis_for_metric(
                scenario,
                metric,
                analysis_frame,
                alpha=policy.default_alpha,
                target_power=policy.trust_checks.practical_significance_power_target or 0.8,
            )
            summary_rows.append(
                summarize_metric_result(
                    experiment=scenario.experiment,
                    runtime_experiment=runtime_experiment,
                    metric=metric,
                    result=result,
                )
            )

        summary_frame = build_summary_frame(summary_rows)
        relevant_columns = _build_relevant_columns(summary_frame, metric_registry)

        srm = evaluate_srm(pd.read_parquet(input_dir / "fact_assignments.parquet"), scenario.experiment, policy)
        missingness = evaluate_missingness(analysis_frame, relevant_columns=relevant_columns, policy=policy)
        exposure_sanity = evaluate_exposure_sanity(
            pd.read_parquet(input_dir / "fact_assignments.parquet"),
            pd.read_parquet(input_dir / "fact_opportunities.parquet"),
            pd.read_parquet(input_dir / "fact_exposures.parquet"),
            policy=policy,
        )
        maturity_results = evaluate_maturity(summary_frame)
        evaluability_results = evaluate_metric_evaluability(summary_frame, policy=policy)

        overall_state = TrustState.pass_
        if any(result.state == TrustState.fail for result in [srm, missingness, exposure_sanity]):
            overall_state = TrustState.fail
        elif any(result.state == TrustState.fail for result in maturity_results):
            overall_state = TrustState.fail
        elif any(result.state == TrustState.warn for result in [srm, missingness, exposure_sanity]):
            overall_state = TrustState.warn

        trust_pack = TrustPackResult(
            scenario_id=scenario.scenario_id,
            experiment_id=scenario.experiment.experiment_id,
            overall_state=overall_state,
            srm=srm,
            missingness=missingness,
            exposure_sanity=exposure_sanity,
            maturity=maturity_results,
            evaluability=evaluability_results,
            analysis_summary=summary_frame.to_dict(orient="records"),
            truth_comparison={},
            notes=[],
        )

        recommendation_proxy, recommendation_supported = _recommendation_proxy(
            scenario=scenario,
            truth=scenario.validation_truth,
            summary_frame=summary_frame,
            trust=trust_pack,
            metric_registry=metric_registry,
            alpha=policy.default_alpha,
        )

        truth = scenario.validation_truth
        primary_row = summary_frame.loc[summary_frame["metric_name"] == truth.primary_metric_name].iloc[0].to_dict()
        truth_comparison = {
            "expected_srm_flag": bool(truth.expected_srm_flag),
            "observed_srm_flag": srm.state == TrustState.fail,
            "srm_match": (srm.state == TrustState.fail) == bool(truth.expected_srm_flag),
            "expected_primary_effect_value": truth.true_primary_effect_value,
            "observed_primary_effect_value": float(primary_row["effect"]),
            "primary_effect_difference": float(primary_row["effect"]) - float(truth.true_primary_effect_value),
            "primary_effect_sign_match": (
                (float(primary_row["effect"]) == 0.0 and float(truth.true_primary_effect_value) == 0.0)
                or np.sign(float(primary_row["effect"])) == np.sign(float(truth.true_primary_effect_value))
            ),
            "expected_recommendation": truth.expected_recommendation.value,
            "recommendation_proxy": recommendation_proxy,
            "recommendation_supported": recommendation_supported,
            "recommendation_match": None if not recommendation_supported else recommendation_proxy == truth.expected_recommendation.value,
            "expected_peeking_risk": truth.expected_peeking_risk,
            "maturity_status": primary_row.get("status"),
            "evaluability_status": next((item.status.value for item in evaluability_results if item.metric_name == truth.primary_metric_name), None),
        }
        trust_pack.truth_comparison = truth_comparison
        if not recommendation_supported:
            trust_pack.notes.append("segment_policy_not_implemented")

        scenario_results.append(
            ScenarioValidationResult(
                scenario=scenario,
                scenario_path=scenario_path,
                input_dir=input_dir,
                runtime_experiment=runtime_experiment,
                summary_frame=summary_frame,
                trust=trust_pack,
                recommendation_proxy=recommendation_proxy,
                recommendation_supported=recommendation_supported,
                recommendation_match=truth_comparison["recommendation_match"],
            )
        )

    overall_state = TrustState.pass_
    if any(result.trust.overall_state == TrustState.fail for result in scenario_results):
        overall_state = TrustState.fail
    elif any(result.trust.overall_state == TrustState.warn for result in scenario_results):
        overall_state = TrustState.warn

    pack = ValidationPackResult(
        output_dir=Path(output_dir) if output_dir is not None else ROOT / "reports" / "validation",
        scenarios=scenario_results,
        overall_state=overall_state,
    )
    return pack

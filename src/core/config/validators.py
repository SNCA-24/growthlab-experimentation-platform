from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..contracts import ExperimentContract, FilterDefinition, MetricContract, PolicyContract, ScenarioContract
from ..filters.filter_compiler import ALLOWED_ANALYTICAL_COLUMNS, compile_filters


def validate_filter_columns(filters: Sequence[FilterDefinition]) -> None:
    unknown_columns = sorted({filter_definition.column for filter_definition in filters if filter_definition.column not in ALLOWED_ANALYTICAL_COLUMNS})
    if unknown_columns:
        raise ValueError(f"unknown filter column(s): {', '.join(unknown_columns)}")


def validate_metric_registry(metrics: Mapping[str, MetricContract]) -> None:
    duplicate_names = [name for name, metric in metrics.items() if name != metric.metric_name]
    if duplicate_names:
        raise ValueError(f"metric registry keys must match metric_name: {', '.join(duplicate_names)}")


def validate_policy_registry(policies: Mapping[str, PolicyContract]) -> None:
    duplicate_ids = [policy_id for policy_id, policy in policies.items() if policy_id != policy.policy_id]
    if duplicate_ids:
        raise ValueError(f"policy registry keys must match policy_id: {', '.join(duplicate_ids)}")


def validate_experiment_contract(experiment: ExperimentContract) -> None:
    validate_filter_columns(experiment.target_population_filters)
    validate_filter_columns(experiment.pre_registered_filters)
    compile_filters(experiment.target_population_filters)
    compile_filters(experiment.pre_registered_filters)
    if not experiment.pre_registered_groupby_columns:
        return
    unknown_groupby = sorted(set(experiment.pre_registered_groupby_columns) - ALLOWED_ANALYTICAL_COLUMNS)
    if unknown_groupby:
        raise ValueError(
            f"experiment '{experiment.experiment_id}' references unknown pre_registered_groupby_columns: {', '.join(unknown_groupby)}"
        )


def validate_experiment_references(
    experiment: ExperimentContract,
    metric_registry: Mapping[str, MetricContract],
    policy_registry: Mapping[str, PolicyContract],
) -> None:
    validate_experiment_contract(experiment)
    metric_ids = [
        experiment.primary_metric,
        *experiment.secondary_metrics,
        *experiment.guardrail_metrics,
        *experiment.diagnostic_metrics,
    ]
    missing_metrics = sorted({metric_id for metric_id in metric_ids if metric_id not in metric_registry})
    if missing_metrics:
        raise ValueError(f"experiment '{experiment.experiment_id}' references unknown metric(s): {', '.join(missing_metrics)}")
    if experiment.decision_policy_id not in policy_registry:
        raise ValueError(
            f"experiment '{experiment.experiment_id}' references unknown policy '{experiment.decision_policy_id}'"
        )


def validate_scenario_contract(scenario: ScenarioContract) -> None:
    if scenario.validation_truth.scenario_id is not None and scenario.scenario_id != scenario.validation_truth.scenario_id:
        raise ValueError("scenario_id must match validation_truth.scenario_id")
    if scenario.validation_truth.experiment_id is not None and scenario.experiment.experiment_id != scenario.validation_truth.experiment_id:
        raise ValueError("experiment.experiment_id must match validation_truth.experiment_id")
    if scenario.experiment.primary_metric != scenario.validation_truth.primary_metric_name:
        raise ValueError("experiment.primary_metric must match validation_truth.primary_metric_name")
    if scenario.experiment.primary_metric not in scenario.metric_generation:
        raise ValueError("metric_generation must include the primary metric")

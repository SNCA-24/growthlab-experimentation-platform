from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TypeVar

from ..contracts import (
    ExperimentContract,
    MetricContract,
    PolicyContract,
    ScenarioContract,
    TableContract,
    YamlContract,
    load_contract_from_yaml,
)
from .validators import (
    validate_experiment_contract,
    validate_experiment_references,
    validate_metric_registry,
    validate_policy_registry,
    validate_scenario_contract,
)

TContract = TypeVar("TContract", bound=YamlContract)


def _iter_yaml_files(path: str | Path) -> list[Path]:
    root = Path(path)
    if root.is_file():
        return [root]
    if not root.exists():
        raise FileNotFoundError(root)
    files = sorted({*root.rglob("*.yaml"), *root.rglob("*.yml")})
    return [file_path for file_path in files if file_path.is_file()]


def _load_registry(
    path: str | Path,
    loader: Callable[[str | Path], TContract],
    key_fn: Callable[[TContract], str],
) -> dict[str, TContract]:
    registry: dict[str, TContract] = {}
    for file_path in _iter_yaml_files(path):
        contract = loader(file_path)
        key = key_fn(contract)
        if key in registry:
            raise ValueError(f"duplicate contract key '{key}' found while loading {file_path}")
        registry[key] = contract
    return registry


def load_experiment_contract(
    path: str | Path,
    *,
    metric_registry: Mapping[str, MetricContract] | None = None,
    policy_registry: Mapping[str, PolicyContract] | None = None,
) -> ExperimentContract:
    contract = load_contract_from_yaml(path, ExperimentContract)
    validate_experiment_contract(contract)
    if metric_registry is not None or policy_registry is not None:
        validate_experiment_references(contract, metric_registry or {}, policy_registry or {})
    return contract


def load_metric_contract(path: str | Path) -> MetricContract:
    return load_contract_from_yaml(path, MetricContract)


def load_policy_contract(path: str | Path) -> PolicyContract:
    return load_contract_from_yaml(path, PolicyContract)


def load_scenario_contract(path: str | Path) -> ScenarioContract:
    contract = load_contract_from_yaml(path, ScenarioContract)
    validate_scenario_contract(contract)
    return contract


def load_experiment_registry(
    path: str | Path,
    *,
    metric_registry: Mapping[str, MetricContract] | None = None,
    policy_registry: Mapping[str, PolicyContract] | None = None,
) -> dict[str, ExperimentContract]:
    experiments = _load_registry(path, load_experiment_contract, lambda contract: contract.experiment_id)
    if metric_registry is not None or policy_registry is not None:
        for contract in experiments.values():
            validate_experiment_references(contract, metric_registry or {}, policy_registry or {})
    return experiments


def load_metric_registry(path: str | Path) -> dict[str, MetricContract]:
    registry = _load_registry(path, load_metric_contract, lambda contract: contract.metric_name)
    validate_metric_registry(registry)
    return registry


def load_policy_registry(path: str | Path) -> dict[str, PolicyContract]:
    registry = _load_registry(path, load_policy_contract, lambda contract: contract.policy_id)
    validate_policy_registry(registry)
    return registry


def load_scenario_registry(path: str | Path) -> dict[str, ScenarioContract]:
    return _load_registry(path, load_scenario_contract, lambda contract: contract.scenario_id)


def load_table_contract(table_name: str) -> type[TableContract]:
    from ..contracts import CANONICAL_TABLE_MODELS

    try:
        return CANONICAL_TABLE_MODELS[table_name]
    except KeyError as exc:
        raise KeyError(f"unknown canonical table: {table_name}") from exc

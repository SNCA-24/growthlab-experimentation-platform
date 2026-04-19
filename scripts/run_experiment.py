#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis.ab.binary import analyze_binary_metric  # noqa: E402
from analysis.ab.continuous import analyze_continuous_metric  # noqa: E402
from analysis.ratios.delta_method import analyze_ratio_metric  # noqa: E402
from core.config.loaders import load_experiment_contract, load_metric_registry, load_policy_registry  # noqa: E402
from core.contracts import DimExperimentsContract, MetricContract, MetricType  # noqa: E402
from reporting.tables.summary import build_summary_frame, build_summary_payload, summarize_metric_result  # noqa: E402


DEFAULT_POLICY_REGISTRY = ROOT / "configs" / "policies"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GrowthLab analysis for a generated synthetic scenario")
    parser.add_argument("--experiment-config", required=True, help="Path to the experiment YAML config")
    parser.add_argument(
        "--metric-registry",
        required=True,
        action="append",
        help="Path to a metric registry directory or YAML file; may be repeated",
    )
    parser.add_argument("--input-parquet-dir", required=True, help="Directory containing canonical parquet outputs")
    parser.add_argument("--output-dir", required=True, help="Directory to write summary artifacts into")
    return parser.parse_args()


def _load_metric_registries(paths: list[str]) -> dict[str, MetricContract]:
    registry: dict[str, MetricContract] = {}
    for path in paths:
        loaded = load_metric_registry(path)
        for metric_name, metric in loaded.items():
            if metric_name in registry:
                raise ValueError(f"duplicate metric registry entry '{metric_name}' across supplied paths")
            registry[metric_name] = metric
    return registry


def _load_input_frames(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame | None, pd.DataFrame]:
    experiment_frame = pd.read_parquet(input_dir / "dim_experiments.parquet")
    user_frame = pd.read_parquet(input_dir / "dim_users.parquet") if (input_dir / "dim_users.parquet").exists() else None
    if (input_dir / "fact_user_outcomes.parquet").exists():
        outcome_frame = pd.read_parquet(input_dir / "fact_user_outcomes.parquet")
    else:
        raise FileNotFoundError(input_dir / "fact_user_outcomes.parquet")
    return experiment_frame, user_frame, outcome_frame


def _normalize_runtime_value(value):
    if isinstance(value, (list, dict, tuple, set)):
        return value
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        return value
    except ValueError:
        return value
    return value


def _analyze_metric(
    experiment,
    metric,
    analysis_frame: pd.DataFrame,
    *,
    alpha: float,
    target_power: float,
):
    if metric.metric_type == MetricType.binary:
        return analyze_binary_metric(experiment, metric, analysis_frame, metric_role="configured", alpha=alpha, target_power=target_power)
    if metric.metric_type == MetricType.continuous:
        return analyze_continuous_metric(experiment, metric, analysis_frame, metric_role="configured", alpha=alpha, target_power=target_power)
    if metric.metric_type == MetricType.ratio:
        return analyze_ratio_metric(experiment, metric, analysis_frame, metric_role="configured", alpha=alpha, target_power=target_power)
    raise TypeError(f"unsupported metric_type: {metric.metric_type}")


def main() -> int:
    args = _parse_args()
    experiment_path = Path(args.experiment_config)
    input_dir = Path(args.input_parquet_dir)
    output_dir = Path(args.output_dir)

    metric_registry = _load_metric_registries(args.metric_registry)
    policy_registry = load_policy_registry(DEFAULT_POLICY_REGISTRY)
    experiment = load_experiment_contract(experiment_path, metric_registry=metric_registry, policy_registry=policy_registry)
    policy = policy_registry[experiment.decision_policy_id]

    runtime_experiments, user_frame, outcome_frame = _load_input_frames(input_dir)
    runtime_experiment = None
    if len(runtime_experiments) > 0:
        runtime_row = runtime_experiments.iloc[0].to_dict()
        runtime_row = {key: _normalize_runtime_value(value) for key, value in runtime_row.items()}
        runtime_experiment = DimExperimentsContract.model_validate(runtime_row)
    analysis_frame = outcome_frame
    if user_frame is not None:
        analysis_frame = analysis_frame.merge(user_frame, on="user_id", how="left", suffixes=("", "_user"))

    metric_order: list[str] = []
    for metric_name in [
        experiment.primary_metric,
        *experiment.secondary_metrics,
        *experiment.guardrail_metrics,
        *experiment.diagnostic_metrics,
    ]:
        if metric_name not in metric_order:
            metric_order.append(metric_name)

    rows: list[dict[str, object]] = []
    for metric_name in metric_order:
        if metric_name not in metric_registry:
            raise ValueError(f"experiment references unknown metric '{metric_name}'")
        metric = metric_registry[metric_name]
        metric_frame = analysis_frame
        result = _analyze_metric(
            experiment,
            metric,
            metric_frame,
            alpha=policy.default_alpha,
            target_power=policy.trust_checks.practical_significance_power_target or 0.8,
        )
        rows.append(
            summarize_metric_result(
                experiment=experiment,
                runtime_experiment=runtime_experiment,
                metric=metric,
                result=result,
            )
        )

    summary_frame = build_summary_frame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_frame.to_parquet(output_dir / "analysis_summary.parquet", index=False)
    payload = build_summary_payload(
        configured_experiment=experiment,
        runtime_experiment=runtime_experiment,
        summary_frame=summary_frame,
        input_dir=str(input_dir),
    )
    (output_dir / "analysis_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=lambda value: value.item() if hasattr(value, "item") else str(value)),
        encoding="utf-8",
    )

    if runtime_experiment is not None and runtime_experiment.experiment_id != experiment.experiment_id:
        print(
            f"configured_experiment_id={experiment.experiment_id} runtime_experiment_id={runtime_experiment.experiment_id} note=mismatch_reported"
        )
    for row in summary_frame.to_dict(orient="records"):
        print(
            f"{row['metric_name']} status={row['status']} effect={row['effect']:.6f} "
            f"ci=[{row['ci_lower']:.6f},{row['ci_upper']:.6f}] p={row['p_value']:.4g} "
            f"cuped={'yes' if row['cuped_enabled'] else 'no'} practical_met={row['practical_threshold_met']}"
        )
    print(f"wrote {len(summary_frame)} metric summaries to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

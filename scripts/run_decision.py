#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from decisioning.policy_engine.engine import run_decision  # noqa: E402
from reporting.artifacts.decision_report import write_decision_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GrowthLab decisioning on an analyzed scenario")
    parser.add_argument("--experiment-config", required=True, help="Path to the experiment YAML config")
    parser.add_argument("--policy-config", required=True, help="Path to the policy YAML config")
    parser.add_argument("--analysis-summary", required=True, help="Path to analysis_summary parquet or json")
    parser.add_argument("--trust-summary", required=True, help="Path to trust_summary or validation_summary json")
    parser.add_argument("--output-dir", required=True, help="Directory to write decision artifacts into")
    parser.add_argument(
        "--metric-registry",
        default=str(ROOT / "configs" / "metrics"),
        help="Path to the metric registry directory or YAML file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_decision(
        experiment_config=args.experiment_config,
        policy_config=args.policy_config,
        analysis_summary=args.analysis_summary,
        trust_summary=args.trust_summary,
        metric_registry_path=args.metric_registry,
        output_dir=args.output_dir,
    )
    payload = write_decision_report(result, args.output_dir)
    print(
        f"final_action={payload['final_action']} stage={payload['decided_stage']} "
        f"scenario_id={payload.get('scenario_id')} output_dir={args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


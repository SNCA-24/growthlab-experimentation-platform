#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.config.loaders import load_experiment_contract, load_metric_registry, load_policy_registry  # noqa: E402
from simulator.scenario_runner.run import run_scenario  # noqa: E402
from validation.harness.reporting import write_validation_reports  # noqa: E402
from validation.harness.run_pack import run_validation_pack  # noqa: E402
from decisioning.policy_engine.engine import run_decision  # noqa: E402
from reporting.artifacts.decision_report import write_decision_report  # noqa: E402


def main() -> int:
    metrics = load_metric_registry(ROOT / "configs" / "metrics")
    policies = load_policy_registry(ROOT / "configs" / "policies")
    experiment = load_experiment_contract(
        ROOT / "configs" / "experiments" / "exp_onboarding_v1.yaml",
        metric_registry=metrics,
        policy_registry=policies,
    )
    assert experiment.experiment_id == "exp_onboarding_v1"
    assert len(metrics) == 8
    assert len(policies) == 1

    scenario_path = ROOT / "configs" / "scenarios" / "scenario_aa_null.yaml"
    with tempfile.TemporaryDirectory(prefix="growthlab-smoke-") as tmp:
        tmp_root = Path(tmp)
        synthetic_dir = tmp_root / "synthetic"
        validation_dir = tmp_root / "validation"
        decision_dir = tmp_root / "decision"

        run_scenario(scenario_path, synthetic_dir)
        expected_tables = [
            "dim_experiments.parquet",
            "dim_users.parquet",
            "fact_assignments.parquet",
            "fact_opportunities.parquet",
            "fact_exposures.parquet",
            "fact_user_day.parquet",
            "fact_user_outcomes.parquet",
            "fact_validation_truth.parquet",
        ]
        for table_name in expected_tables:
            assert (synthetic_dir / table_name).exists(), f"missing {table_name}"

        pack = run_validation_pack([synthetic_dir], output_dir=validation_dir)
        write_validation_reports(pack)
        assert pack.overall_state.value == "pass"
        assert len(pack.scenarios) == 1

        scenario_output_dir = validation_dir / "scenario_aa_null"
        analysis_summary = scenario_output_dir / "analysis_summary.json"
        validation_summary = scenario_output_dir / "validation_summary.json"
        assert analysis_summary.exists()
        assert validation_summary.exists()

        decision = run_decision(
            experiment_config=ROOT / "configs" / "experiments" / "exp_onboarding_v1.yaml",
            policy_config=ROOT / "configs" / "policies" / "growth_default_v1.yaml",
            analysis_summary=analysis_summary,
            trust_summary=validation_summary,
            output_dir=decision_dir,
            input_parquet_dir=synthetic_dir,
        )
        write_decision_report(decision, decision_dir)
        assert decision.final_action.value == "HOLD_INCONCLUSIVE"
        assert (decision_dir / "decision_summary.json").exists()
        assert (decision_dir / "decision_summary.md").exists()

    print("smoke tests passed: config loading, generation, validation, decisioning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

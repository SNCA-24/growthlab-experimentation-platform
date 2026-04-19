#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.config.loaders import load_scenario_contract  # noqa: E402
from reporting.artifacts.export import export_artifact_manifest, export_scenario_bundle  # noqa: E402

DEFAULT_SCENARIOS = [
    "scenario_aa_null",
    "scenario_global_positive",
    "scenario_guardrail_harm",
    "scenario_segment_only_win",
    "scenario_srm_invalid",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build GrowthLab demo artifacts")
    parser.add_argument("--output-dir", default=str(ROOT / "reports" / "demo"), help="Directory to write demo artifacts into")
    parser.add_argument(
        "--scenarios",
        nargs="*",
        default=DEFAULT_SCENARIOS,
        help="Scenario IDs to include in the demo bundle",
    )
    return parser.parse_args()


def _copy_if_exists(src: Path, dst: Path) -> Path | None:
    if not src.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def _scenario_paths(scenario_id: str) -> dict[str, Path]:
    validation_root = ROOT / "reports" / "validation" / "full_pack" / scenario_id
    decision_root = ROOT / "reports" / "decision" / scenario_id
    return {
        "scenario": ROOT / "configs" / "scenarios" / f"{scenario_id}.yaml",
        "validation_json": validation_root / "validation_summary.json",
        "validation_md": validation_root / "validation_summary.md",
        "trust_json": validation_root / "trust_summary.json",
        "trust_md": validation_root / "trust_summary.md",
        "analysis_json": validation_root / "analysis_summary.json",
        "analysis_parquet": validation_root / "analysis_summary.parquet",
        "decision_json": decision_root / "decision_summary.json",
        "decision_md": decision_root / "decision_summary.md",
        "decision_csv": decision_root / "decision_summary.csv",
        "guardrail_csv": decision_root / "guardrail_summary.csv",
        "segment_csv": decision_root / "segment_summary.csv",
    }


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries: list[dict[str, str | None]] = []
    for scenario_id in args.scenarios:
        paths = _scenario_paths(scenario_id)
        if not paths["validation_json"].exists():
            raise FileNotFoundError(f"missing validation artifacts for {scenario_id}")
        if not paths["decision_json"].exists():
            raise FileNotFoundError(f"missing decision artifacts for {scenario_id}")

        scenario_dir = output_dir / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        scenario_copy = _copy_if_exists(paths["scenario"], scenario_dir / paths["scenario"].name)
        scenario_contract = load_scenario_contract(paths["scenario"]) if paths["scenario"].exists() else None
        validation = json.loads(paths["validation_json"].read_text(encoding="utf-8"))
        trust = json.loads(paths["trust_json"].read_text(encoding="utf-8"))
        decision = json.loads(paths["decision_json"].read_text(encoding="utf-8"))
        if paths["analysis_json"].exists():
            analysis_payload = json.loads(paths["analysis_json"].read_text(encoding="utf-8"))
            analysis_rows = analysis_payload.get("records") if isinstance(analysis_payload, dict) else analysis_payload
        else:
            analysis_rows = decision.get("metric_summary_rows") or []

        export_scenario_bundle(
            output_dir=scenario_dir,
            scenario_id=scenario_id,
            scenario_name=scenario_contract.scenario_name if scenario_contract is not None else validation.get("scenario_name") or scenario_id,
            scenario_path=str(scenario_copy or paths["scenario"]),
            validation_summary=validation,
            trust_summary=trust,
            decision_summary=decision,
            analysis_rows=analysis_rows or [],
            source_paths={
                "validation_summary": str(paths["validation_json"]),
                "trust_summary": str(paths["trust_json"]),
                "decision_summary": str(paths["decision_json"]),
                "analysis_summary": str(paths["analysis_json"]),
            },
        )

        manifest_entries.append(
            {
                "scenario_id": scenario_id,
                "scenario_name": validation.get("scenario_name") or scenario_id,
                "scenario_path": str(scenario_copy or paths["scenario"]),
                "validation_summary_path": str(scenario_dir / "validation_summary.json"),
                "trust_summary_path": str(scenario_dir / "trust_summary.json"),
                "analysis_summary_path": str(scenario_dir / "analysis_summary.json"),
                "decision_summary_path": str(scenario_dir / "decision_summary.json"),
            }
        )

    manifest = {"scenarios": manifest_entries}
    export_artifact_manifest(output_dir / "manifest.json", manifest)
    print(f"built {len(manifest_entries)} demo scenarios in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

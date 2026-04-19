from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd

from decisioning.actions.render import render_decision_markdown
from reporting.tables.summary import compact_decision_table, compact_guardrail_table, compact_segment_table, compact_metric_table


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True, default=str))


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def export_decision_bundle(
    *,
    output_dir: str | Path,
    decision_payload: dict[str, Any],
    analysis_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    json_path = out_dir / "decision_summary.json"
    md_path = out_dir / "decision_summary.md"
    write_json(json_path, decision_payload)
    md_path.write_text(render_decision_markdown(decision_payload), encoding="utf-8")
    paths["decision_json"] = json_path
    paths["decision_md"] = md_path

    if analysis_rows is not None:
        analysis_frame = pd.DataFrame(analysis_rows)
        csv_path = out_dir / "analysis_summary.csv"
        write_csv(csv_path, compact_metric_table(analysis_frame))
        paths["analysis_csv"] = csv_path

    guardrail_rows = decision_payload.get("guardrail_summary") or []
    if guardrail_rows:
        guardrail_path = out_dir / "guardrail_summary.csv"
        write_csv(guardrail_path, pd.DataFrame(guardrail_rows))
        paths["guardrail_csv"] = guardrail_path

    segment_payload = decision_payload.get("segment_summary")
    segment_frame = compact_segment_table(segment_payload)
    if not segment_frame.empty:
        segment_path = out_dir / "segment_summary.csv"
        write_csv(segment_path, segment_frame)
        paths["segment_csv"] = segment_path

    decision_frame = compact_decision_table(decision_payload)
    write_csv(out_dir / "decision_summary.csv", decision_frame)
    paths["decision_csv"] = out_dir / "decision_summary.csv"
    return paths


def export_artifact_manifest(path: str | Path, payload: dict[str, Any]) -> Path:
    out_path = Path(path)
    write_json(out_path, payload)
    return out_path


def export_scenario_bundle(
    *,
    output_dir: str | Path,
    scenario_id: str,
    scenario_name: str,
    scenario_path: str | None,
    validation_summary: dict[str, Any],
    trust_summary: dict[str, Any],
    decision_summary: dict[str, Any],
    analysis_rows: list[dict[str, Any]],
    source_paths: dict[str, str] | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "scenario_path": scenario_path,
        "validation_summary_path": source_paths.get("validation_summary") if source_paths else None,
        "trust_summary_path": source_paths.get("trust_summary") if source_paths else None,
        "decision_summary_path": source_paths.get("decision_summary") if source_paths else None,
        "analysis_summary_path": source_paths.get("analysis_summary") if source_paths else None,
    }
    export_artifact_manifest(out_dir / "manifest.json", payload)
    write_json(out_dir / "validation_summary.json", validation_summary)
    write_json(out_dir / "trust_summary.json", trust_summary)
    write_json(out_dir / "decision_summary.json", decision_summary)
    (out_dir / "validation_summary.md").write_text(
        "# Validation Summary\n\n"
        f"- scenario_id: `{validation_summary.get('scenario_id')}`\n"
        f"- overall_state: `{validation_summary.get('overall_state')}`\n"
        f"- recommendation_proxy: `{validation_summary.get('recommendation_proxy')}`\n",
        encoding="utf-8",
    )
    (out_dir / "trust_summary.md").write_text(
        "# Trust Summary\n\n"
        f"- scenario_id: `{trust_summary.get('scenario_id')}`\n"
        f"- overall_state: `{trust_summary.get('overall_state')}`\n",
        encoding="utf-8",
    )
    (out_dir / "decision_summary.md").write_text(render_decision_markdown(decision_summary), encoding="utf-8")
    analysis_frame = pd.DataFrame(analysis_rows)
    write_json(out_dir / "analysis_summary.json", {"records": analysis_frame.to_dict(orient="records")})
    write_csv(out_dir / "analysis_summary.csv", compact_metric_table(analysis_frame))
    write_csv(out_dir / "decision_summary.csv", compact_decision_table(decision_summary))
    if decision_summary.get("guardrail_summary"):
        write_csv(out_dir / "guardrail_summary.csv", pd.DataFrame(decision_summary["guardrail_summary"]))
    segment_frame = compact_segment_table(decision_summary.get("segment_summary"))
    if not segment_frame.empty:
        write_csv(out_dir / "segment_summary.csv", segment_frame)
    return {
        "manifest": out_dir / "manifest.json",
        "validation_summary": out_dir / "validation_summary.json",
        "trust_summary": out_dir / "trust_summary.json",
        "decision_summary": out_dir / "decision_summary.json",
        "analysis_summary": out_dir / "analysis_summary.csv",
    }

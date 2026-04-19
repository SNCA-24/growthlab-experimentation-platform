from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from core.config.loaders import load_policy_contract, load_scenario_contract  # noqa: E402
from reporting.tables.summary import compact_decision_table, compact_metric_table  # noqa: E402
from ui.pages import (  # noqa: E402
    render_decision_page,
    render_guardrails_page,
    render_overview_page,
    render_primary_metrics_page,
    render_segment_analysis_page,
    render_trust_checks_page,
)
from ui.pages.downloads import render_downloads_page  # noqa: E402


DEFAULT_DEMO_ROOT = ROOT / "reports" / "demo"
DEFAULT_VALIDATION_ROOT = ROOT / "reports" / "validation" / "full_pack"
DEFAULT_DECISION_ROOT = ROOT / "reports" / "decision"
DEFAULT_SCENARIO_ROOT = ROOT / "configs" / "scenarios"
DEFAULT_POLICY_ROOT = ROOT / "configs" / "policies"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_source_path(entry: dict[str, Any], key: str, fallback: Path | None = None) -> Path | None:
    value = entry.get(key)
    if value:
        path = Path(value)
        if path.exists():
            return path
    if fallback is not None and fallback.exists():
        return fallback
    return None


def _discover_manifest(demo_root: Path = DEFAULT_DEMO_ROOT) -> list[dict[str, Any]]:
    manifest_path = demo_root / "manifest.json"
    if manifest_path.exists():
        manifest = _load_json(manifest_path)
        return list(manifest.get("scenarios", []))

    entries: list[dict[str, Any]] = []
    if DEFAULT_DECISION_ROOT.exists():
        for decision_path in sorted(DEFAULT_DECISION_ROOT.glob("*/decision_summary.json")):
            scenario_id = decision_path.parent.name
            validation_path = DEFAULT_VALIDATION_ROOT / scenario_id / "validation_summary.json"
            analysis_path = decision_path.parent / "analysis_summary.json"
            trust_path = decision_path.parent / "trust_summary.json"
            scenario_path = DEFAULT_SCENARIO_ROOT / f"{scenario_id}.yaml"
            entries.append(
                {
                    "scenario_id": scenario_id,
                    "scenario_path": str(scenario_path) if scenario_path.exists() else None,
                    "decision_summary_path": str(decision_path),
                    "validation_summary_path": str(validation_path) if validation_path.exists() else None,
                    "analysis_summary_path": str(analysis_path) if analysis_path.exists() else None,
                    "trust_summary_path": str(trust_path) if trust_path.exists() else None,
                }
            )
    return entries


def _load_scenario_bundle(entry: dict[str, Any]) -> dict[str, Any]:
    scenario_path_value = entry.get("scenario_path")
    if not scenario_path_value:
        scenario_path_value = str(DEFAULT_SCENARIO_ROOT / f"{entry['scenario_id']}.yaml")
    scenario_path = Path(scenario_path_value)
    scenario = load_scenario_contract(scenario_path)

    validation_path = _resolve_source_path(entry, "validation_summary_path", DEFAULT_VALIDATION_ROOT / scenario.scenario_id / "validation_summary.json")
    trust_path = _resolve_source_path(entry, "trust_summary_path", DEFAULT_VALIDATION_ROOT / scenario.scenario_id / "trust_summary.json")
    decision_path = _resolve_source_path(entry, "decision_summary_path", DEFAULT_DECISION_ROOT / scenario.scenario_id / "decision_summary.json")
    analysis_path = _resolve_source_path(entry, "analysis_summary_path", DEFAULT_DECISION_ROOT / scenario.scenario_id / "analysis_summary.json")

    validation = _load_json(validation_path) if validation_path and validation_path.exists() else {}
    trust = _load_json(trust_path) if trust_path and trust_path.exists() else (validation.get("trust") or {})
    decision = _load_json(decision_path) if decision_path and decision_path.exists() else {}
    analysis = _load_json(analysis_path) if analysis_path and analysis_path.exists() else {}

    if not analysis and decision.get("metric_summary_rows"):
        analysis = {"records": decision["metric_summary_rows"]}

    analysis_rows = analysis.get("records") if isinstance(analysis, dict) else analysis
    analysis_frame = pd.DataFrame(analysis_rows or [])
    policy_path = DEFAULT_POLICY_ROOT / f"{scenario.experiment.decision_policy_id}.yaml"
    policy = load_policy_contract(policy_path) if policy_path.exists() else None

    return {
        "scenario": scenario,
        "policy": policy,
        "validation": validation,
        "trust": trust if trust else validation.get("trust", {}),
        "decision": decision,
        "analysis": analysis,
        "analysis_rows": analysis_rows or [],
        "analysis_frame": analysis_frame,
        "paths": {
            "validation_json": validation_path,
            "trust_json": trust_path,
            "decision_json": decision_path,
            "analysis_json": analysis_path,
            "validation_md": (validation_path.with_suffix(".md") if validation_path else None),
            "trust_md": (trust_path.with_suffix(".md") if trust_path else None),
            "decision_md": (decision_path.with_suffix(".md") if decision_path else None),
            "decision_csv": (decision_path.parent / "decision_summary.csv"),
            "guardrail_csv": (decision_path.parent / "guardrail_summary.csv"),
            "segment_csv": (decision_path.parent / "segment_summary.csv"),
        },
    }


def _scenario_label(entry: dict[str, Any]) -> str:
    scenario_id = entry.get("scenario_id", "unknown")
    scenario_path = entry.get("scenario_path")
    if scenario_path:
        try:
            scenario = load_scenario_contract(scenario_path)
            return f"{scenario.scenario_name} ({scenario_id})"
        except Exception:
            pass
    return str(scenario_id)


def _prepare_page_context(bundle: dict[str, Any]) -> dict[str, Any]:
    decision = bundle.get("decision") or {}
    analysis_rows = bundle.get("analysis_rows") or []
    analysis_frame = bundle.get("analysis_frame")
    if analysis_frame is None or getattr(analysis_frame, "empty", False) and not analysis_rows:
        analysis_frame = pd.DataFrame(analysis_rows)
    return {
        "scenario": bundle["scenario"],
        "policy": bundle.get("policy"),
        "validation": bundle.get("validation") or {},
        "trust": bundle.get("trust") or {},
        "decision": decision,
        "analysis": {"records": analysis_rows},
        "analysis_rows": analysis_rows,
        "analysis_frame": analysis_frame,
        "paths": bundle.get("paths") or {},
    }


def main() -> None:
    st.set_page_config(page_title="GrowthLab", layout="wide")
    st.title("GrowthLab")
    st.caption("Local-first experimentation UI over the shared analysis, trust, and decision artifacts.")

    manifest = _discover_manifest()
    if not manifest:
        st.warning("No demo artifacts found. Run `scripts/build_demo_artifacts.py` first.")
        return

    scenario_labels = [_scenario_label(entry) for entry in manifest]
    selected_label = st.sidebar.selectbox("Scenario", scenario_labels, index=0)
    selected_index = scenario_labels.index(selected_label)
    bundle = _load_scenario_bundle(manifest[selected_index])
    context = _prepare_page_context(bundle)

    st.sidebar.write(f"Scenario ID: `{bundle['scenario'].scenario_id}`")
    st.sidebar.write(f"Final action: `{bundle.get('decision', {}).get('final_action', 'N/A')}`")
    if bundle.get("policy") is not None:
        st.sidebar.write(f"Policy: `{bundle['policy'].policy_id}`")

    tabs = st.tabs(["Overview", "Trust Checks", "Primary Metrics", "Guardrails", "Segment Analysis", "Decision", "Downloads"])
    with tabs[0]:
        render_overview_page(context)
    with tabs[1]:
        render_trust_checks_page(context)
    with tabs[2]:
        render_primary_metrics_page(context)
    with tabs[3]:
        render_guardrails_page(context)
    with tabs[4]:
        render_segment_analysis_page(context)
    with tabs[5]:
        render_decision_page(context)
    with tabs[6]:
        render_downloads_page(context)


if __name__ == "__main__":
    main()

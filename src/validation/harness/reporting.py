from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..trust._models import to_jsonable


def _format_bool(value: Any) -> str:
    if value is True:
        return "PASS"
    if value is False:
        return "FAIL"
    return "N/A"


def render_scenario_markdown(result: Any) -> str:
    trust = result.trust
    summary_frame: pd.DataFrame = result.summary_frame
    primary_metric_name = result.scenario.experiment.primary_metric
    primary_rows = summary_frame.loc[summary_frame["metric_name"] == primary_metric_name]
    primary_row = primary_rows.iloc[0].to_dict() if not primary_rows.empty else {}
    lines: list[str] = []
    lines.append(f"# {result.scenario.scenario_name}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- scenario_id: `{result.scenario.scenario_id}`")
    lines.append(f"- scenario_type: `{result.scenario.scenario_type.value}`")
    lines.append(f"- input_dir: `{result.input_dir}`")
    lines.append(f"- trust_status: `{trust.overall_state.value}`")
    lines.append(f"- recommendation_proxy: `{result.recommendation_proxy}`" if result.recommendation_proxy else "- recommendation_proxy: `not evaluated`")
    lines.append("")
    lines.append("## Trust Checks")
    lines.append(f"- SRM: `{trust.srm.state.value}` ({trust.srm.message})")
    lines.append(f"- Missingness: `{trust.missingness.state.value}` ({trust.missingness.message})")
    lines.append(f"- Exposure sanity: `{trust.exposure_sanity.state.value}` ({trust.exposure_sanity.message})")
    lines.append(f"- Maturity: `{', '.join(item.maturity_status for item in trust.maturity)}`")
    lines.append(f"- Evaluability: `{', '.join(item.status.value for item in trust.evaluability)}`")
    lines.append("")
    lines.append("## Validation Truth")
    truth = result.scenario.validation_truth
    lines.append(f"- expected_srm_flag: `{truth.expected_srm_flag}`")
    lines.append(f"- expected_recommendation: `{truth.expected_recommendation.value}`")
    lines.append(f"- expected_peeking_risk: `{truth.expected_peeking_risk}`")
    lines.append("")
    lines.append("## Primary Metric")
    if primary_row:
        lines.append(f"- metric_name: `{primary_row.get('metric_name')}`")
        lines.append(f"- effect: `{primary_row.get('effect')}`")
        lines.append(f"- ci: `[{primary_row.get('ci_lower')}, {primary_row.get('ci_upper')}]`")
        lines.append(f"- p_value: `{primary_row.get('p_value')}`")
        lines.append(f"- practical_threshold_met: `{primary_row.get('practical_threshold_met')}`")
    lines.append("")
    lines.append("## Metrics")
    table_columns = ["metric_name", "metric_role", "effect", "ci_lower", "ci_upper", "p_value", "status"]
    lines.append("| " + " | ".join(table_columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(table_columns)) + " |")
    for row in summary_frame[table_columns].to_dict(orient="records"):
        lines.append(
            "| "
            + " | ".join(
                str(row[column]) for column in table_columns
            )
            + " |"
        )
    return "\n".join(lines)


def render_pack_markdown(pack: Any) -> str:
    lines: list[str] = []
    lines.append("# GrowthLab Validation Pack")
    lines.append("")
    lines.append(f"- overall_state: `{pack.overall_state.value}`")
    lines.append(f"- scenarios: `{len(pack.scenarios)}`")
    lines.append("")
    lines.append("## Scenarios")
    for scenario in pack.scenarios:
        lines.append(f"- `{scenario.scenario.scenario_id}`: `{scenario.trust.overall_state.value}`")
    return "\n".join(lines)


def write_validation_reports(pack: Any) -> None:
    output_root = Path(pack.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    scenario_payloads: list[dict[str, Any]] = []
    for scenario in pack.scenarios:
        scenario_dir = output_root / scenario.scenario.scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        scenario.summary_frame.to_parquet(scenario_dir / "analysis_summary.parquet", index=False)
        (scenario_dir / "analysis_summary.json").write_text(
            json.dumps(scenario.summary_frame.to_dict(orient="records"), indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )

        trust_payload = to_jsonable(scenario.trust)
        (scenario_dir / "trust_summary.json").write_text(
            json.dumps(trust_payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        (scenario_dir / "trust_summary.md").write_text(render_scenario_markdown(scenario), encoding="utf-8")

        validation_payload = {
            "scenario_id": scenario.scenario.scenario_id,
            "scenario_type": scenario.scenario.scenario_type.value,
            "input_dir": str(scenario.input_dir),
            "scenario_path": str(scenario.scenario_path),
            "overall_state": scenario.trust.overall_state.value,
            "recommendation_proxy": scenario.recommendation_proxy,
            "recommendation_supported": scenario.recommendation_supported,
            "recommendation_match": scenario.recommendation_match,
            "truth_comparison": scenario.trust.truth_comparison,
            "trust": trust_payload,
        }
        (scenario_dir / "validation_summary.json").write_text(
            json.dumps(validation_payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        (scenario_dir / "validation_summary.md").write_text(render_scenario_markdown(scenario), encoding="utf-8")
        scenario_payloads.append(validation_payload)

    pack_payload = {
        "overall_state": pack.overall_state.value,
        "scenarios": scenario_payloads,
    }
    (output_root / "validation_pack.json").write_text(
        json.dumps(pack_payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    (output_root / "validation_pack.md").write_text(render_pack_markdown(pack), encoding="utf-8")

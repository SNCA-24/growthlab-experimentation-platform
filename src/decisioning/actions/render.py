from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _format_list(values: Iterable[Any]) -> str:
    items = [str(value) for value in values if value is not None]
    return ", ".join(items) if items else "none"


def render_decision_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# GrowthLab Decision Report")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- final_action: `{payload.get('final_action')}`")
    lines.append(f"- decided_stage: `{payload.get('decided_stage')}`")
    lines.append(f"- scenario_id: `{payload.get('scenario_id')}`")
    lines.append(f"- experiment_id: `{payload.get('experiment_id')}`")
    lines.append(f"- policy_id: `{payload.get('policy_id')}`")
    lines.append(f"- trust_state: `{payload.get('trust_state')}`")
    lines.append(f"- recommendation_supported: `{payload.get('recommendation_supported', True)}`")
    lines.append("")

    lines.append("## Reason Codes")
    lines.append(f"- {_format_list(payload.get('reason_codes', []))}")
    lines.append("")

    trust = payload.get("trust_summary", {})
    lines.append("## Trust Summary")
    lines.append(f"- SRM: `{trust.get('srm_state')}` ({trust.get('srm_message')})")
    lines.append(f"- Missingness: `{trust.get('missingness_state')}` ({trust.get('missingness_message')})")
    lines.append(f"- Exposure sanity: `{trust.get('exposure_state')}` ({trust.get('exposure_message')})")
    lines.append(f"- Maturity: `{trust.get('primary_maturity_status')}`")
    lines.append(f"- Evaluability: `{trust.get('primary_evaluability_status')}`")
    lines.append("")

    primary = payload.get("primary_metric_summary", {})
    lines.append("## Primary Metric")
    lines.append(f"- metric_name: `{primary.get('metric_name')}`")
    lines.append(f"- effect: `{primary.get('effect')}`")
    lines.append(f"- ci: `[{primary.get('ci_lower')}, {primary.get('ci_upper')}]`")
    lines.append(f"- p_value: `{primary.get('p_value')}`")
    lines.append(f"- practical_threshold_met: `{primary.get('practical_threshold_met')}`")
    lines.append(f"- practical_threshold_value: `{primary.get('practical_threshold_value')}`")
    lines.append("")

    guardrails = payload.get("guardrail_summary", [])
    if guardrails:
        lines.append("## Guardrails")
        for row in guardrails:
            lines.append(
                f"- `{row.get('metric_name')}`: state=`{row.get('state')}`, effect=`{row.get('effect')}`, "
                f"ci=`[{row.get('ci_lower')}, {row.get('ci_upper')}]`"
            )
        lines.append("")

    business = payload.get("business_value_summary", {})
    lines.append("## Business Value")
    lines.append(f"- expected_value: `{business.get('expected_value')}`")
    lines.append(f"- threshold: `{business.get('threshold')}`")
    lines.append(f"- state: `{business.get('state')}`")
    lines.append("")

    segment = payload.get("segment_summary")
    if segment:
        lines.append("## Segment Policy")
        lines.append(f"- state: `{segment.get('state')}`")
        lines.append(f"- selected_segments: `{_format_list(segment.get('selected_segments', []))}`")
        lines.append(f"- correction_method: `{segment.get('correction_method')}`")
        lines.append(f"- interaction_threshold: `{segment.get('interaction_p_value_threshold')}`")
        lines.append("")

    return "\n".join(lines)


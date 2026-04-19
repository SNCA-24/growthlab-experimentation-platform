from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from reporting.charts.plots import guardrail_figure
from reporting.tables.summary import compact_guardrail_table


def render_guardrails_page(context: dict[str, Any]) -> None:
    decision = context.get("decision", {})
    analysis = context.get("analysis", {})
    scenario = context["scenario"]
    rows = analysis.get("records") or context.get("analysis_rows") or []
    guardrail_metrics = list(scenario.experiment.guardrail_metrics)

    st.subheader("Guardrails")
    frame = compact_guardrail_table(pd.DataFrame(rows), guardrail_metrics)
    if frame.empty:
        st.warning("No guardrail rows available.")
        return
    st.plotly_chart(guardrail_figure(frame), use_container_width=True)
    st.dataframe(frame, use_container_width=True, hide_index=True)

    guardrail_summary = decision.get("guardrail_summary") or []
    if guardrail_summary:
        st.caption(f"Policy stage: {decision.get('decided_stage')} | Guardrail result: {guardrail_summary[0].get('state', 'unknown')}")

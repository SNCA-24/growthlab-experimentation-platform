from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from reporting.charts.plots import primary_metric_figure
from reporting.tables.summary import compact_metric_table


def render_primary_metrics_page(context: dict[str, Any]) -> None:
    decision = context.get("decision", {})
    analysis = context.get("analysis", {})
    primary = decision.get("primary_metric_summary") or {}
    rows = analysis.get("records") or context.get("analysis_rows") or []

    st.subheader("Primary Metrics")
    if not primary:
        st.warning("Primary metric summary unavailable.")
        return

    cols = st.columns(4)
    cols[0].metric("Effect", f"{float(primary.get('effect') or 0.0):.6f}")
    cols[1].metric("CI lower", f"{float(primary.get('ci_lower') or 0.0):.6f}")
    cols[2].metric("CI upper", f"{float(primary.get('ci_upper') or 0.0):.6f}")
    cols[3].metric("p-value", f"{float(primary.get('p_value') or 1.0):.4f}")

    st.plotly_chart(primary_metric_figure(primary), use_container_width=True)

    frame = compact_metric_table(pd.DataFrame(rows))
    if not frame.empty:
        st.dataframe(frame.loc[frame["metric_role"] == "primary"], use_container_width=True, hide_index=True)

    cuped_enabled = primary.get("cuped_enabled")
    if cuped_enabled:
        cuped_cols = st.columns(4)
        cuped_cols[0].metric("CUPED effect", f"{float(primary.get('cuped_effect') or 0.0):.6f}")
        cuped_cols[1].metric("CUPED CI lower", f"{float(primary.get('cuped_ci_lower') or 0.0):.6f}")
        cuped_cols[2].metric("CUPED CI upper", f"{float(primary.get('cuped_ci_upper') or 0.0):.6f}")
        cuped_cols[3].metric("CUPED p-value", f"{float(primary.get('cuped_p_value') or 1.0):.4f}")

    maturity_exclusions = {
        "total_n": primary.get("total_n"),
        "mature_n": primary.get("mature_n"),
        "immature_n": primary.get("immature_n"),
        "status": primary.get("status"),
    }
    st.caption(f"Maturity exclusions: {maturity_exclusions}")

from __future__ import annotations

from typing import Any

import streamlit as st

from reporting.charts.plots import segment_figure
from reporting.tables.summary import compact_segment_table


def render_segment_analysis_page(context: dict[str, Any]) -> None:
    decision = context.get("decision", {})
    segment_summary = decision.get("segment_summary") or {}
    st.subheader("Segment Analysis")

    selected = segment_summary.get("selected_segments") or []
    st.metric("Targeted rollout allowed", "Yes" if selected else "No")
    st.caption("Only pre-registered segment outputs are shown here.")

    frame = compact_segment_table(segment_summary)
    if frame.empty:
        st.info("No segment candidates available.")
        return
    st.plotly_chart(segment_figure(frame), use_container_width=True)
    st.dataframe(frame, use_container_width=True, hide_index=True)


from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go


def primary_metric_figure(primary_row: dict[str, Any]) -> go.Figure:
    fig = go.Figure()
    metric_name = str(primary_row.get("metric_name", "primary"))
    effect = float(primary_row.get("effect") or 0.0)
    ci_lower = float(primary_row.get("ci_lower") or 0.0)
    ci_upper = float(primary_row.get("ci_upper") or 0.0)
    fig.add_trace(
        go.Scatter(
            x=[effect],
            y=[metric_name],
            mode="markers",
            marker=dict(size=12, color="#1f77b4"),
            error_x=dict(type="data", array=[max(ci_upper - effect, 0.0)], arrayminus=[max(effect - ci_lower, 0.0)]),
            name="effect",
        )
    )
    fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="#777")
    fig.update_layout(
        title="Primary metric effect",
        xaxis_title="Effect",
        yaxis_title="",
        height=240,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )
    return fig


def guardrail_figure(guardrail_frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if guardrail_frame.empty:
        fig.update_layout(title="Guardrails", height=220, margin=dict(l=20, r=20, t=40, b=20))
        return fig
    fig.add_trace(
        go.Bar(
            x=guardrail_frame["metric_name"].astype(str),
            y=guardrail_frame["effect"].astype(float),
            marker_color="#d95f02",
            name="effect",
        )
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#777")
    fig.update_layout(
        title="Guardrail metric effects",
        xaxis_title="Metric",
        yaxis_title="Effect",
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )
    return fig


def segment_figure(segment_frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if segment_frame.empty:
        fig.update_layout(title="Segment analysis", height=220, margin=dict(l=20, r=20, t=40, b=20))
        return fig
    fig.add_trace(
        go.Bar(
            x=segment_frame["segment_key"].astype(str),
            y=segment_frame["effect"].astype(float),
            marker_color=["#2ca02c" if bool(selected) else "#9e9e9e" for selected in segment_frame.get("selected", [])],
            name="effect",
        )
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#777")
    fig.update_layout(
        title="Pre-registered segment effects",
        xaxis_title="Segment",
        yaxis_title="Effect",
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )
    return fig


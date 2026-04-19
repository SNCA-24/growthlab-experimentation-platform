from __future__ import annotations

from typing import Any

import streamlit as st


def render_overview_page(context: dict[str, Any]) -> None:
    scenario = context["scenario"]
    decision = context.get("decision", {})
    experiment = scenario.experiment
    primary_action = decision.get("final_action", "N/A")

    st.subheader("Overview")
    st.markdown(f"**Scenario:** {scenario.scenario_name}")
    st.caption(f"{scenario.description or ''}")

    cols = st.columns(3)
    cols[0].metric("Experiment", experiment.experiment_id)
    cols[1].metric("Primary metric", experiment.primary_metric)
    cols[2].metric("Policy", experiment.decision_policy_id)

    cols = st.columns(3)
    cols[0].metric("Estimand", experiment.primary_estimand.value)
    cols[1].metric("Analysis mode", experiment.analysis_mode.value)
    cols[2].metric("Final action", primary_action)

    explanation = decision.get("reason_codes") or []
    if explanation:
        st.info(" | ".join(str(item) for item in explanation[:4]))
    else:
        st.info("No decision artifact loaded.")


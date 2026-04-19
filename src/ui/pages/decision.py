from __future__ import annotations

from typing import Any

import streamlit as st

from reporting.tables.summary import compact_decision_table


def _plain_explanation(action: str | None) -> str:
    mapping = {
        "INVESTIGATE_INVALID_EXPERIMENT": "The experiment failed trust checks and should not be treated as decisionable.",
        "HOLD_GUARDRAIL_RISK": "Primary movement is not enough because a guardrail risk is present.",
        "HOLD_INCONCLUSIVE": "The evidence is not strong enough to commit to a ship decision.",
        "RERUN_UNDERPOWERED": "The experiment needs more sample or maturity before a final read.",
        "SHIP_GLOBAL": "The overall evidence is strong enough to ship globally.",
        "SHIP_TARGETED_SEGMENTS": "The effect is strong enough in approved segments to support a targeted rollout.",
    }
    return mapping.get(action or "", "No plain-language explanation available.")


def render_decision_page(context: dict[str, Any]) -> None:
    decision = context.get("decision", {})
    st.subheader("Decision")
    action = decision.get("final_action")
    stage = decision.get("decided_stage")
    reason_codes = decision.get("reason_codes") or []

    cols = st.columns(3)
    cols[0].metric("Final action", str(action))
    cols[1].metric("Decided stage", str(stage))
    cols[2].metric("Trust state", str(decision.get("trust_state", "unknown")))

    st.info(_plain_explanation(action))
    if reason_codes:
        st.write("Reason codes:")
        st.code("\n".join(str(code) for code in reason_codes), language="text")
    st.dataframe(compact_decision_table(decision), use_container_width=True, hide_index=True)


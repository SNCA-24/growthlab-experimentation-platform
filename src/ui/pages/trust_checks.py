from __future__ import annotations

from typing import Any

import streamlit as st

from reporting.tables.summary import compact_trust_table


def render_trust_checks_page(context: dict[str, Any]) -> None:
    trust = context.get("trust", {})
    validation = context.get("validation", {})
    trust_payload = trust if trust else (validation.get("trust") or {})
    trust_summary = trust_payload.get("truth_comparison", {})
    st.subheader("Trust Checks")

    cols = st.columns(4)
    cols[0].metric("SRM", str(trust_payload.get("srm", {}).get("state", trust_payload.get("srm_state", "N/A"))))
    cols[1].metric("Missingness", str(trust_payload.get("missingness", {}).get("state", trust_payload.get("missingness_state", "N/A"))))
    cols[2].metric("Maturity", str(trust_payload.get("maturity", [{}])[0].get("maturity_status", trust_payload.get("primary_maturity_status", "N/A"))))
    cols[3].metric("Evaluability", str(trust_payload.get("evaluability", [{}])[0].get("status", trust_payload.get("primary_evaluability_status", "N/A"))))

    summary_frame = compact_trust_table(
        {
            "srm_state": trust_payload.get("srm", {}).get("state", trust_payload.get("srm_state")),
            "srm_message": trust_payload.get("srm", {}).get("message", trust_payload.get("srm_message")),
            "missingness_state": trust_payload.get("missingness", {}).get("state", trust_payload.get("missingness_state")),
            "missingness_message": trust_payload.get("missingness", {}).get("message", trust_payload.get("missingness_message")),
            "exposure_state": trust_payload.get("exposure_sanity", {}).get("state", trust_payload.get("exposure_state")),
            "exposure_message": trust_payload.get("exposure_sanity", {}).get("message", trust_payload.get("exposure_message")),
            "primary_maturity_status": (trust_payload.get("maturity", [{}])[0].get("maturity_status") if trust_payload.get("maturity") else trust_payload.get("primary_maturity_status")),
            "primary_evaluability_status": (trust_payload.get("evaluability", [{}])[0].get("status") if trust_payload.get("evaluability") else trust_payload.get("primary_evaluability_status")),
        }
    )
    st.dataframe(summary_frame, use_container_width=True, hide_index=True)

    if trust_summary:
        st.caption(f"Recommendation proxy: {trust_summary.get('recommendation_proxy')}")


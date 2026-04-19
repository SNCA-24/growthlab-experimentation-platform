from __future__ import annotations

import pandas as pd

from core.contracts.policy_contracts import PolicyContract

from ._models import ExposureSanityResult, TrustState


def evaluate_exposure_sanity(
    assignments: pd.DataFrame,
    opportunities: pd.DataFrame,
    exposures: pd.DataFrame,
    *,
    policy: PolicyContract,
) -> ExposureSanityResult:
    trust = policy.trust_checks
    if not trust.enabled or not trust.require_exposure_opportunity_sanity:
        return ExposureSanityResult(
            state=TrustState.pass_,
            assignments_n=len(assignments),
            opportunity_users=len(opportunities),
            exposure_users=len(exposures),
            opportunity_rate=0.0,
            exposure_rate=0.0,
            exposure_to_opportunity_rate=None,
            inconsistent_exposure_rows=0,
            inconsistent_opportunity_rows=0,
            message="exposure_sanity_disabled",
        )

    assignments_key = assignments[["experiment_id", "user_id", "assigned_group"]].copy()
    opportunity_key = opportunities[["experiment_id", "user_id"]].copy() if not opportunities.empty else opportunities.copy()
    exposure_key = exposures[["experiment_id", "user_id", "assigned_group", "variant_served"]].copy() if not exposures.empty else exposures.copy()

    opportunity_join = opportunity_key.merge(assignments_key, on=["experiment_id", "user_id"], how="left", indicator=True)
    inconsistent_opportunity_rows = int((opportunity_join["_merge"] != "both").sum())
    if "assigned_group_x" in opportunity_join.columns and "assigned_group_y" in opportunity_join.columns:
        inconsistent_opportunity_rows += int(
            (opportunity_join["assigned_group_x"].astype(str) != opportunity_join["assigned_group_y"].astype(str)).sum()
        )

    exposure_join = exposure_key.merge(assignments_key, on=["experiment_id", "user_id"], how="left", indicator=True)
    inconsistent_exposure_rows = int((exposure_join["_merge"] != "both").sum())
    if "assigned_group_x" in exposure_join.columns and "assigned_group_y" in exposure_join.columns:
        inconsistent_exposure_rows += int(
            (exposure_join["assigned_group_x"].astype(str) != exposure_join["assigned_group_y"].astype(str)).sum()
        )
    if "variant_served" in exposure_join.columns and "assigned_group_y" in exposure_join.columns:
        inconsistent_exposure_rows += int(
            (exposure_join["variant_served"].astype(str) != exposure_join["assigned_group_y"].astype(str)).sum()
        )

    assignments_n = len(assignments)
    opportunity_users = len(opportunities)
    exposure_users = len(exposures)
    opportunity_rate = opportunity_users / assignments_n if assignments_n else 0.0
    exposure_rate = exposure_users / assignments_n if assignments_n else 0.0
    exposure_to_opportunity_rate = exposure_users / opportunity_users if opportunity_users else None

    has_inconsistency = (
        inconsistent_opportunity_rows > 0
        or inconsistent_exposure_rows > 0
        or exposure_rate > opportunity_rate + 1e-9
    )
    state = TrustState.fail if has_inconsistency else TrustState.pass_
    message = "exposure_opportunity_inconsistent" if has_inconsistency else "exposure_opportunity_sane"

    return ExposureSanityResult(
        state=state,
        assignments_n=assignments_n,
        opportunity_users=opportunity_users,
        exposure_users=exposure_users,
        opportunity_rate=opportunity_rate,
        exposure_rate=exposure_rate,
        exposure_to_opportunity_rate=exposure_to_opportunity_rate,
        inconsistent_exposure_rows=inconsistent_exposure_rows,
        inconsistent_opportunity_rows=inconsistent_opportunity_rows,
        message=message,
    )


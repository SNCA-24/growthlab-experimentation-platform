from __future__ import annotations

import numpy as np
import pandas as pd

from core.contracts import ScenarioContract

from ._shared import OpportunityGenerationState, datetime_series_to_day_index


def generate_fact_opportunities(
    scenario: ScenarioContract,
    dim_users: pd.DataFrame,
    fact_assignments: pd.DataFrame,
    rng: np.random.Generator,
) -> OpportunityGenerationState:
    trigger_probability = scenario.opportunity_and_delivery.trigger_probability
    assignment_ts = pd.to_datetime(fact_assignments["assignment_ts"], utc=True)
    triggered = rng.random(len(fact_assignments)) < trigger_probability
    user_row_index = np.flatnonzero(triggered)
    assigned_group = fact_assignments.loc[triggered, "assigned_group"].to_numpy()

    opportunity_users = fact_assignments.loc[triggered, ["experiment_id", "user_id", "assigned_group", "assignment_ts"]].copy()
    opportunity_users["opportunity_count"] = 1
    opportunity_users["first_opportunity_flag"] = 1
    opportunity_users["surface"] = scenario.opportunity_and_delivery.exposure_surface
    opportunity_users["opportunity_source"] = "session_start"

    delay_seconds = rng.integers(0, 3 * 60 * 60, size=len(opportunity_users), endpoint=False, dtype=np.int32)
    opportunity_users["opportunity_ts"] = pd.to_datetime(opportunity_users["assignment_ts"], utc=True) + pd.to_timedelta(
        delay_seconds, unit="s"
    )
    opportunity_users = opportunity_users.drop(columns=["assignment_ts"])

    analysis_start_date = scenario.experiment.assignment_start_ts_utc.date()
    first_opportunity_ts = pd.Series(pd.NaT, index=fact_assignments.index, dtype="datetime64[ns, UTC]")
    first_opportunity_ts.loc[triggered] = opportunity_users["opportunity_ts"].to_numpy()
    first_opportunity_day_index = np.full(len(fact_assignments), -1, dtype=np.int32)
    first_opportunity_day_index[triggered] = datetime_series_to_day_index(opportunity_users["opportunity_ts"], analysis_start_date)

    had_opportunity = triggered.astype(np.int8)

    table = opportunity_users[
        [
            "experiment_id",
            "user_id",
            "opportunity_ts",
            "surface",
            "opportunity_count",
            "first_opportunity_flag",
            "opportunity_source",
        ]
    ].reset_index(drop=True)

    return OpportunityGenerationState(
        table=table,
        user_row_index=user_row_index,
        assigned_group=assigned_group,
        had_opportunity=had_opportunity,
        first_opportunity_ts=first_opportunity_ts,
        first_opportunity_day_index=first_opportunity_day_index,
    )

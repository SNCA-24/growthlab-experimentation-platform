from __future__ import annotations

import numpy as np
import pandas as pd

from core.contracts import ScenarioContract

from ._shared import ExposureGenerationState, datetime_series_to_day_index


def generate_fact_exposures(
    scenario: ScenarioContract,
    fact_assignments: pd.DataFrame,
    opportunities: ExposureGenerationState,
    rng: np.random.Generator,
) -> ExposureGenerationState:
    opportunity_table = opportunities.table
    if opportunity_table.empty:
        empty = pd.DataFrame(
            columns=[
                "experiment_id",
                "user_id",
                "opportunity_ts",
                "exposure_ts",
                "assigned_group",
                "variant_served",
                "delivery_status",
                "exposure_count",
                "first_exposure_flag",
                "surface",
            ]
        )
        return ExposureGenerationState(
            table=empty,
            user_row_index=np.zeros(0, dtype=np.int32),
            is_exposed=np.zeros(len(fact_assignments), dtype=np.int8),
            first_exposure_ts=pd.Series(pd.NaT, index=fact_assignments.index, dtype="datetime64[ns, UTC]"),
            first_exposure_day_index=np.full(len(fact_assignments), -1, dtype=np.int32),
        )

    delivery_control = scenario.opportunity_and_delivery.delivery_probability_control
    delivery_treatment = scenario.opportunity_and_delivery.delivery_probability_treatment
    delivered_probability = np.where(
        opportunities.assigned_group == "control",
        delivery_control,
        delivery_treatment,
    )
    exposed = rng.random(len(opportunity_table)) < delivered_probability

    exposed_table = opportunity_table.loc[exposed].copy()
    exposed_table["assigned_group"] = opportunities.assigned_group[exposed]
    exposed_table["variant_served"] = opportunities.assigned_group[exposed]
    exposed_table["delivery_status"] = "shown"
    delay_seconds = rng.integers(60, 60 * 60, size=len(exposed_table), endpoint=False, dtype=np.int32)
    exposed_table["exposure_ts"] = pd.to_datetime(exposed_table["opportunity_ts"], utc=True) + pd.to_timedelta(
        delay_seconds, unit="s"
    )
    exposed_table["exposure_count"] = 1
    exposed_table["first_exposure_flag"] = 1
    exposed_table["surface"] = scenario.opportunity_and_delivery.exposure_surface

    is_exposed = np.zeros(len(fact_assignments), dtype=np.int8)
    exposed_user_row_index = opportunities.user_row_index[exposed]
    is_exposed[exposed_user_row_index] = 1

    first_exposure_ts = pd.Series(pd.NaT, index=fact_assignments.index, dtype="datetime64[ns, UTC]")
    first_exposure_ts.iloc[exposed_user_row_index] = exposed_table["exposure_ts"].to_numpy()
    first_exposure_day_index = np.full(len(fact_assignments), -1, dtype=np.int32)
    first_exposure_day_index[exposed_user_row_index] = datetime_series_to_day_index(
        exposed_table["exposure_ts"], scenario.experiment.assignment_start_ts_utc.date()
    )

    table = exposed_table[
        [
            "experiment_id",
            "user_id",
            "opportunity_ts",
            "exposure_ts",
            "assigned_group",
            "variant_served",
            "delivery_status",
            "exposure_count",
            "first_exposure_flag",
            "surface",
        ]
    ].reset_index(drop=True)

    return ExposureGenerationState(
        table=table,
        user_row_index=exposed_user_row_index,
        is_exposed=is_exposed,
        first_exposure_ts=first_exposure_ts,
        first_exposure_day_index=first_exposure_day_index,
    )

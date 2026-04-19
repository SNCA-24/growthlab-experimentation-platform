from __future__ import annotations

import numpy as np
import pandas as pd

from core.contracts import ScenarioContract

from ._shared import UserDayGenerationState, datetime_series_to_day_index


def _primary_outcome_for_metric(
    metric_name: str,
    conversions_7d: np.ndarray,
    retention_7d: np.ndarray,
    revenue_30d: np.ndarray,
    engagement_7d: np.ndarray,
) -> np.ndarray:
    if metric_name == "conversion_7d":
        return conversions_7d.astype(np.float32)
    if metric_name == "retention_7d":
        return retention_7d.astype(np.float32)
    if metric_name == "revenue_30d":
        return revenue_30d.astype(np.float32)
    if metric_name == "engagement_7d":
        return engagement_7d.astype(np.float32)
    return conversions_7d.astype(np.float32)


def generate_fact_user_outcomes(
    scenario: ScenarioContract,
    dim_users: pd.DataFrame,
    fact_assignments: pd.DataFrame,
    opportunities,
    exposures,
    user_day: UserDayGenerationState,
) -> pd.DataFrame:
    experiment = scenario.experiment
    analysis_start_date = experiment.assignment_start_ts_utc.date()
    analysis_end_date = experiment.observation_end_ts_utc.date()
    n_days = int((analysis_end_date - analysis_start_date).days)

    user_day_table = user_day.table.copy()
    user_day_table["date"] = pd.to_datetime(user_day_table["date"], utc=True).dt.date

    anchor_day_index = np.where(
        opportunities.first_opportunity_day_index >= 0,
        opportunities.first_opportunity_day_index,
        datetime_series_to_day_index(fact_assignments["assignment_ts"], analysis_start_date),
    )

    date_index = pd.date_range(start=analysis_start_date, end=analysis_end_date, freq="D", inclusive="left", tz="UTC")
    day_index_2d = np.broadcast_to(np.arange(n_days, dtype=np.int32), (len(dim_users), n_days))
    anchor_2d = anchor_day_index[:, None]
    within_7d = (day_index_2d >= anchor_2d) & (day_index_2d < anchor_2d + 7)
    within_30d = (day_index_2d >= anchor_2d) & (day_index_2d < anchor_2d + 30)

    sessions = user_day_table["sessions"].to_numpy().reshape(len(dim_users), n_days)
    revenue = user_day_table["revenue"].to_numpy().reshape(len(dim_users), n_days)
    content = user_day_table["content_consumption_minutes"].to_numpy().reshape(len(dim_users), n_days)
    converted = user_day_table["converted"].to_numpy().reshape(len(dim_users), n_days)
    retained_d7 = user_day_table["retained_d7_flag"].to_numpy().reshape(len(dim_users), n_days)
    notif_clicked = user_day_table["notif_clicked"].to_numpy().reshape(len(dim_users), n_days)
    uninstall = user_day_table["guardrail_uninstall_flag"].to_numpy().reshape(len(dim_users), n_days)
    support = user_day_table["guardrail_support_ticket_flag"].to_numpy().reshape(len(dim_users), n_days)

    sessions_7d = (sessions * within_7d).sum(axis=1).astype(np.int32)
    sessions_30d = (sessions * within_30d).sum(axis=1).astype(np.int32)
    revenue_30d = (revenue * within_30d).sum(axis=1).astype(np.float32)
    engagement_7d = (content * within_7d).sum(axis=1).astype(np.float32)
    conversions_7d = converted.sum(axis=1).astype(np.int32)
    retention_7d = retained_d7.sum(axis=1).astype(np.int32)
    clicks_7d = notif_clicked.sum(axis=1).astype(np.int32)
    uninstalls_7d = uninstall.sum(axis=1).astype(np.int32)
    support_tickets_7d = support.sum(axis=1).astype(np.int32)

    impressions_7d = np.maximum(sessions_7d * 2 + clicks_7d, 1).astype(np.int32)

    first_opportunity_ts = opportunities.first_opportunity_ts
    first_exposure_ts = exposures.first_exposure_ts
    first_opportunity_day_index = opportunities.first_opportunity_day_index

    days_since_first_opportunity = np.where(
        first_opportunity_day_index >= 0,
        np.maximum((n_days - 1) - first_opportunity_day_index, 0),
        0,
    ).astype(np.int32)

    primary_outcome_value = _primary_outcome_for_metric(
        experiment.primary_metric,
        conversions_7d,
        retention_7d,
        revenue_30d,
        engagement_7d,
    )

    table = pd.DataFrame(
        {
            "experiment_id": experiment.experiment_id,
            "user_id": dim_users["user_id"].to_numpy(),
            "assigned_group": fact_assignments["assigned_group"].astype(str).to_numpy(),
            "had_opportunity": opportunities.had_opportunity.astype(np.int8),
            "is_exposed": exposures.is_exposed.astype(np.int8),
            "first_opportunity_ts": first_opportunity_ts,
            "first_exposure_ts": first_exposure_ts,
            "days_since_first_opportunity": days_since_first_opportunity,
            "analysis_window_days": np.full(len(dim_users), min(30, n_days), dtype=np.int16),
            "primary_outcome_value": primary_outcome_value.astype(np.float32),
            "primary_outcome_name": np.repeat(experiment.primary_metric, len(dim_users)),
            "conversions_7d": conversions_7d,
            "sessions_7d": sessions_7d,
            "sessions_30d": sessions_30d,
            "impressions_7d": impressions_7d,
            "clicks_7d": clicks_7d,
            "retention_7d": retention_7d,
            "retention_30d": user_day.retention_30d_flag.astype(np.int8),
            "revenue_30d": revenue_30d,
            "engagement_7d": engagement_7d,
            "guardrail_1_value": pd.Series([None] * len(dim_users), dtype="object"),
            "guardrail_2_value": pd.Series([None] * len(dim_users), dtype="object"),
            "support_tickets_7d": support_tickets_7d,
            "uninstalls_7d": uninstalls_7d,
        }
    )

    return table

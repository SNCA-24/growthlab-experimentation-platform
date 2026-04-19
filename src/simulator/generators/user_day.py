from __future__ import annotations

import numpy as np
import pandas as pd

from core.contracts import ScenarioContract

from ._shared import (
    ExposureGenerationState,
    OpportunityGenerationState,
    UserDayGenerationState,
    datetime_series_to_day_index,
    extract_segment_effect_map,
)


def _event_day_flags(event_day_index: np.ndarray, n_days: int) -> np.ndarray:
    flags = np.zeros((event_day_index.shape[0], n_days), dtype=np.int8)
    valid = event_day_index >= 0
    if valid.any():
        row_index = np.flatnonzero(valid)
        flags[row_index, event_day_index[valid]] = 1
    return flags


def _distribute_total_across_window(
    rng: np.random.Generator,
    totals: np.ndarray,
    after_event_mask: np.ndarray,
    shape: float,
    scale: float,
) -> np.ndarray:
    weights = rng.gamma(shape=shape, scale=scale, size=after_event_mask.shape).astype(np.float32) * after_event_mask
    row_sum = weights.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    return (totals[:, None] * weights / row_sum).astype(np.float32)


def _sample_gamma_totals(rng: np.random.Generator, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    mean = np.asarray(mean, dtype=np.float32)
    std = np.asarray(std, dtype=np.float32)
    safe_std = np.clip(std, 1e-3, None)
    shape = np.clip((mean / safe_std) ** 2, 0.5, None)
    scale = np.where(shape > 0, mean / shape, mean)
    return rng.gamma(shape=shape, scale=np.clip(scale, 1e-6, None)).astype(np.float32)


def generate_fact_user_day(
    scenario: ScenarioContract,
    dim_users: pd.DataFrame,
    fact_assignments: pd.DataFrame,
    opportunities: OpportunityGenerationState,
    exposures: ExposureGenerationState,
    rng: np.random.Generator,
) -> UserDayGenerationState:
    experiment = scenario.experiment
    analysis_start_date = experiment.assignment_start_ts_utc.date()
    analysis_end_date = experiment.observation_end_ts_utc.date()
    date_index = pd.date_range(start=analysis_start_date, end=analysis_end_date, freq="D", inclusive="left", tz="UTC")
    n_days = len(date_index)
    n_users = len(dim_users)

    day_index_2d = np.broadcast_to(np.arange(n_days, dtype=np.int32), (n_users, n_days))

    assignment_day_index = datetime_series_to_day_index(fact_assignments["assignment_ts"], analysis_start_date)
    first_opportunity_day_index = opportunities.first_opportunity_day_index
    first_exposure_day_index = exposures.first_exposure_day_index
    anchor_day_index = np.where(first_opportunity_day_index >= 0, first_opportunity_day_index, assignment_day_index)
    anchor_2d = anchor_day_index[:, None]
    after_anchor = day_index_2d >= anchor_2d
    within_7d = after_anchor & (day_index_2d < anchor_2d + 7)
    within_30d = after_anchor & (day_index_2d < anchor_2d + 30)

    assignment_group = fact_assignments["assigned_group"].to_numpy()
    treatment_mask = assignment_group == "treatment"
    opportunity_mask = opportunities.had_opportunity.astype(bool)
    treated_opportunity_mask = treatment_mask & opportunity_mask

    sessions_base = np.clip(dim_users["historical_sessions_28d"].to_numpy(dtype=np.float32) / 28.0, 0.0, None)
    sessions_lambda = np.clip(sessions_base[:, None] * after_anchor, 0.0, None)
    sessions_daily = rng.poisson(lam=sessions_lambda).astype(np.int16)
    days_active_daily = (sessions_daily > 0).astype(np.int8)

    engagement_effect = extract_segment_effect_map(scenario, "engagement_7d", dim_users)
    engagement_total = _sample_gamma_totals(
        rng,
        np.full(n_users, scenario.metric_generation["engagement_7d"].baseline_mean or 38.0, dtype=np.float32),
        np.full(n_users, scenario.metric_generation["engagement_7d"].baseline_std or 17.0, dtype=np.float32),
    )
    engagement_total *= np.where(treated_opportunity_mask, 1.0 + engagement_effect, 1.0)
    engagement_total = np.clip(
        engagement_total
        * np.clip(
            1.0
            + 0.10 * (dim_users["historical_retention_score"].to_numpy(dtype=np.float32) - 0.5),
            0.5,
            1.5,
        ),
        0.0,
        None,
    )
    content_consumption_minutes = _distribute_total_across_window(rng, engagement_total, within_7d, shape=2.0, scale=1.0)

    revenue_effect = extract_segment_effect_map(scenario, "revenue_30d", dim_users)
    revenue_mean = _sample_gamma_totals(
        rng,
        np.full(n_users, scenario.metric_generation["revenue_30d"].baseline_mean or 1.85, dtype=np.float32),
        np.full(n_users, scenario.metric_generation["revenue_30d"].baseline_std or 7.5, dtype=np.float32),
    )
    revenue_multiplier = np.where(treated_opportunity_mask, 1.0 + revenue_effect, 1.0)
    revenue_total = revenue_mean * revenue_multiplier
    revenue_total *= np.clip(
        1.0 + 0.15 * (dim_users["historical_revenue_28d"].to_numpy(dtype=np.float32) > 0).astype(np.float32),
        1.0,
        1.15,
    )
    outlier_mask = rng.random(n_users) < scenario.data_quality_and_noise.outlier_revenue_rate
    revenue_total[outlier_mask] *= scenario.data_quality_and_noise.outlier_revenue_multiplier
    revenue_daily = _distribute_total_across_window(rng, revenue_total, within_30d, shape=1.5, scale=1.0)

    conversion_effect = extract_segment_effect_map(scenario, "conversion_7d", dim_users)
    conversion_baseline = scenario.metric_generation["conversion_7d"].baseline_rate or 0.028
    historical_sessions_signal = dim_users["historical_sessions_28d"].to_numpy(dtype=np.float32)
    sessions_z = (historical_sessions_signal - historical_sessions_signal.mean()) / (historical_sessions_signal.std() + 1e-6)
    conversion_prob = np.clip(
        conversion_baseline
        + np.where(treated_opportunity_mask, conversion_effect, 0.0)
        + 0.002 * np.tanh(sessions_z),
        0.0,
        1.0,
    )
    converted = rng.random(n_users) < conversion_prob
    conversion_day_index = np.where(converted & (anchor_day_index + 2 < n_days), anchor_day_index + 2, -1)
    converted_daily = _event_day_flags(conversion_day_index, n_days)

    retention_7d_effect = extract_segment_effect_map(scenario, "retention_7d", dim_users)
    retention_7d_baseline = scenario.metric_generation["retention_7d"].baseline_rate or 0.23
    retention_7d_prob = np.clip(
        retention_7d_baseline
        + np.where(treated_opportunity_mask, retention_7d_effect, 0.0)
        + 0.05 * (dim_users["historical_retention_score"].to_numpy(dtype=np.float32) - 0.5),
        0.0,
        1.0,
    )
    retained_7d = rng.random(n_users) < retention_7d_prob
    retained_7d_day_index = np.where(retained_7d & (anchor_day_index + 6 < n_days), anchor_day_index + 6, -1)
    retained_d7_daily = _event_day_flags(retained_7d_day_index, n_days)

    retention_30d_effect = extract_segment_effect_map(scenario, "retention_30d", dim_users)
    retention_30d_baseline = scenario.metric_generation["retention_30d"].baseline_rate or 0.11
    retention_30d_prob = np.clip(
        retention_30d_baseline
        + np.where(treated_opportunity_mask, retention_30d_effect, 0.0)
        + 0.04 * (dim_users["historical_retention_score"].to_numpy(dtype=np.float32) - 0.5),
        0.0,
        1.0,
    )
    retained_30d_flag = (rng.random(n_users) < retention_30d_prob).astype(np.int8)

    d1_prob = np.clip(0.5 * retention_7d_prob, 0.0, 1.0)
    retained_d1 = rng.random(n_users) < d1_prob
    retained_d1_day_index = np.where(retained_d1 & (anchor_day_index + 1 < n_days), anchor_day_index + 1, -1)
    retained_d1_daily = _event_day_flags(retained_d1_day_index, n_days)

    uninstall_effect = extract_segment_effect_map(scenario, "uninstall_rate", dim_users)
    uninstall_prob = np.clip(
        scenario.metric_generation["uninstall_rate"].baseline_rate or 0.012
        + np.where(treated_opportunity_mask, uninstall_effect, 0.0),
        0.0,
        1.0,
    )
    uninstalls_7d = rng.random(n_users) < uninstall_prob
    uninstall_day_index = np.where(uninstalls_7d & (anchor_day_index + 3 < n_days), anchor_day_index + 3, -1)
    uninstall_daily = _event_day_flags(uninstall_day_index, n_days)

    support_effect = extract_segment_effect_map(scenario, "support_ticket_rate", dim_users)
    support_prob = np.clip(
        scenario.metric_generation["support_ticket_rate"].baseline_rate or 0.018
        + np.where(treated_opportunity_mask, support_effect, 0.0),
        0.0,
        1.0,
    )
    support_tickets_7d = rng.random(n_users) < support_prob
    support_day_index = np.where(support_tickets_7d & (anchor_day_index + 4 < n_days), anchor_day_index + 4, -1)
    support_daily = _event_day_flags(support_day_index, n_days)

    notif_prob = np.clip(0.12 + 0.02 * treated_opportunity_mask.astype(np.float32), 0.0, 1.0)
    notif_clicked = rng.random(n_users) < notif_prob
    notif_day_index = np.where(notif_clicked & (anchor_day_index + 2 < n_days), anchor_day_index + 2, -1)
    notif_daily = _event_day_flags(notif_day_index, n_days)

    had_opportunity_daily = _event_day_flags(first_opportunity_day_index, n_days)
    is_exposed_daily = _event_day_flags(first_exposure_day_index, n_days)

    table = pd.DataFrame(
        {
            "date": np.tile(np.asarray(date_index.date, dtype=object), n_users),
            "experiment_id": np.repeat(experiment.experiment_id, n_users * n_days),
            "user_id": np.repeat(dim_users["user_id"].to_numpy(), n_days),
            "assigned_group": np.repeat(assignment_group, n_days),
            "had_opportunity": had_opportunity_daily.reshape(-1),
            "is_exposed": is_exposed_daily.reshape(-1),
            "sessions": sessions_daily.reshape(-1),
            "days_active": days_active_daily.reshape(-1),
            "revenue": revenue_daily.reshape(-1).astype(np.float32),
            "converted": converted_daily.reshape(-1),
            "retained_d1_flag": retained_d1_daily.reshape(-1),
            "retained_d7_flag": retained_d7_daily.reshape(-1),
            "notif_clicked": notif_daily.reshape(-1),
            "guardrail_uninstall_flag": uninstall_daily.reshape(-1),
            "guardrail_support_ticket_flag": support_daily.reshape(-1),
            "content_consumption_minutes": content_consumption_minutes.reshape(-1).astype(np.float32),
            "refund_flag": np.zeros(n_users * n_days, dtype=np.int8),
            "latency_complaint_flag": np.zeros(n_users * n_days, dtype=np.int8),
        }
    )

    return UserDayGenerationState(
        table=table,
        revenue_30d_total=revenue_total.astype(np.float32),
        engagement_7d_total=engagement_total.astype(np.float32),
        retention_30d_flag=retained_30d_flag,
    )

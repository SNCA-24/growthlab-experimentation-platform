from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from core.contracts import ScenarioContract

from ._shared import (
    sample_beta,
    sample_categorical,
    sample_lognormal_mean_sigma,
    sample_truncated_exponential_days,
    sample_zero_inflated_lognormal,
)


def generate_dim_users(scenario: ScenarioContract, rng: np.random.Generator) -> pd.DataFrame:
    population = scenario.population
    baseline = scenario.baseline_behavior
    experiment_start_date = scenario.experiment.assignment_start_ts_utc.date()

    n_users = population.n_users
    user_index = np.arange(n_users, dtype=np.int32)

    country = sample_categorical(rng, population.country_distribution, n_users)
    platform = sample_categorical(rng, population.platform_distribution, n_users)
    acquisition_channel = sample_categorical(rng, population.acquisition_channel_distribution, n_users)
    plan_tier = sample_categorical(rng, population.plan_tier_distribution, n_users)
    tenure_days = sample_truncated_exponential_days(
        rng,
        n_users,
        max_days=population.tenure_days_distribution.max_days,
    )

    historical_sessions_28d = sample_lognormal_mean_sigma(
        rng,
        np.full(n_users, baseline.historical_sessions_28d.mean or 8.0, dtype=np.float64),
        baseline.historical_sessions_28d.sigma or 1.0,
    )
    historical_revenue_28d = sample_zero_inflated_lognormal(
        rng,
        np.full(n_users, baseline.historical_revenue_28d.mean or 1.0, dtype=np.float64),
        baseline.historical_revenue_28d.sigma or 1.0,
        baseline.historical_revenue_28d.zero_rate or 0.0,
    )
    historical_conversion_flag = rng.binomial(
        1,
        baseline.historical_conversion_flag.bernoulli_p or 0.0,
        size=n_users,
    ).astype(np.int8)
    historical_retention_score = sample_beta(
        rng,
        baseline.historical_retention_score.alpha or 1.0,
        baseline.historical_retention_score.beta or 1.0,
        size=n_users,
    )

    signup_date = pd.Series(
        [experiment_start_date - timedelta(days=int(value)) for value in tenure_days],
        dtype="object",
    )

    engagement_cluster = pd.cut(
        historical_sessions_28d,
        bins=[-np.inf, np.quantile(historical_sessions_28d, 0.33), np.quantile(historical_sessions_28d, 0.66), np.inf],
        labels=["low", "medium", "high"],
        include_lowest=True,
    ).astype("object")

    risk_score_baseline = np.clip(1.0 - historical_retention_score + rng.normal(0.0, 0.05, size=n_users), 0.0, 1.0)

    device_class = np.where(platform == "web", "desktop", "mobile")
    region = np.where(country == "US", "NA", "NA")

    return pd.DataFrame(
        {
            "user_id": [f"u_{idx:06d}" for idx in user_index],
            "signup_date": signup_date,
            "country": country,
            "platform": platform,
            "acquisition_channel": acquisition_channel,
            "plan_tier": plan_tier,
            "tenure_days_at_experiment_start": tenure_days.astype(np.int32),
            "historical_sessions_28d": historical_sessions_28d.astype(np.float32),
            "historical_revenue_28d": historical_revenue_28d.astype(np.float32),
            "historical_conversion_flag": historical_conversion_flag.astype(np.int8),
            "historical_retention_score": historical_retention_score.astype(np.float32),
            "device_class": device_class,
            "region": region,
            "risk_score_baseline": risk_score_baseline.astype(np.float32),
            "engagement_cluster": engagement_cluster,
        }
    )

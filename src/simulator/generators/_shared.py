from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from typing import Any

import numpy as np
import pandas as pd

from core.contracts import FilterDefinition, ScenarioContract
from core.filters.filter_compiler import compile_filters


@dataclass(slots=True)
class OpportunityGenerationState:
    table: pd.DataFrame
    user_row_index: np.ndarray
    assigned_group: np.ndarray
    had_opportunity: np.ndarray
    first_opportunity_ts: pd.Series
    first_opportunity_day_index: np.ndarray


@dataclass(slots=True)
class ExposureGenerationState:
    table: pd.DataFrame
    user_row_index: np.ndarray
    is_exposed: np.ndarray
    first_exposure_ts: pd.Series
    first_exposure_day_index: np.ndarray


@dataclass(slots=True)
class UserDayGenerationState:
    table: pd.DataFrame
    revenue_30d_total: np.ndarray
    engagement_7d_total: np.ndarray
    retention_30d_flag: np.ndarray


def safe_probability(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def normalize_weights(weights: dict[str, float]) -> tuple[list[str], np.ndarray]:
    labels = list(weights.keys())
    values = np.asarray([weights[label] for label in labels], dtype=np.float64)
    total = values.sum()
    if total <= 0:
        raise ValueError("distribution weights must sum to a positive value")
    return labels, values / total


def sample_categorical(rng: np.random.Generator, weights: dict[str, float], size: int) -> np.ndarray:
    labels, probabilities = normalize_weights(weights)
    return rng.choice(np.asarray(labels, dtype=object), size=size, p=probabilities)


def sample_truncated_exponential_days(
    rng: np.random.Generator,
    size: int,
    max_days: int,
    scale_days: float | None = None,
) -> np.ndarray:
    scale = float(scale_days if scale_days is not None else max(1.0, max_days / 3.0))
    samples = np.floor(rng.exponential(scale=scale, size=size)).astype(np.int32)
    return np.clip(samples, 0, max_days - 1)


def sample_lognormal_mean_sigma(rng: np.random.Generator, mean: np.ndarray, sigma: float) -> np.ndarray:
    mean = np.asarray(mean, dtype=np.float64)
    sigma = float(sigma)
    mu = np.log(np.clip(mean, 1e-6, None)) - 0.5 * sigma**2
    return rng.lognormal(mean=mu, sigma=sigma).astype(np.float32)


def sample_zero_inflated_lognormal(
    rng: np.random.Generator,
    mean: np.ndarray,
    sigma: float,
    zero_rate: float,
) -> np.ndarray:
    mean = np.asarray(mean, dtype=np.float64)
    sigma = float(sigma)
    zero_rate = safe_probability(zero_rate)
    mu = np.log(np.clip(mean, 1e-6, None)) - 0.5 * sigma**2
    values = rng.lognormal(mean=mu, sigma=sigma).astype(np.float32)
    zero_mask = rng.random(size=values.shape[0]) < zero_rate
    values[zero_mask] = 0.0
    return values


def sample_beta(rng: np.random.Generator, alpha: float, beta: float, size: int) -> np.ndarray:
    return rng.beta(alpha, beta, size=size).astype(np.float32)


def datetime_series_to_day_index(series: pd.Series, start_date: date) -> np.ndarray:
    values = pd.to_datetime(series, utc=True)
    dates = values.dt.floor("D").dt.date
    return np.array([(item - start_date).days for item in dates], dtype=np.int32)


def build_target_population_rule(filters: list[FilterDefinition]) -> str:
    return compile_filters(filters)


def build_filter_payload(filters: list[FilterDefinition]) -> list[dict[str, Any]]:
    return [filter_definition.model_dump(mode="python") for filter_definition in filters]


def serialize_json_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True)


def extract_segment_effect_map(
    scenario: ScenarioContract,
    metric_name: str,
    user_frame: pd.DataFrame,
) -> np.ndarray:
    metric_config = scenario.metric_generation[metric_name]
    base_absolute = float(metric_config.treatment_effect_absolute or 0.0)
    base_relative = float(metric_config.treatment_effect_relative or 0.0)

    if metric_config.treatment_effect_absolute is not None:
        effects = np.full(len(user_frame), base_absolute, dtype=np.float32)
    elif metric_config.treatment_effect_relative is not None:
        effects = np.full(len(user_frame), base_relative, dtype=np.float32)
    else:
        effects = np.zeros(len(user_frame), dtype=np.float32)

    overrides = scenario.segment_effect_overrides
    for segment_dimension, segment_map in overrides.items():
        if segment_dimension not in user_frame.columns:
            continue
        segment_values = user_frame[segment_dimension].astype(str).to_numpy()
        segment_delta = np.zeros(len(user_frame), dtype=np.float32)
        has_override = np.zeros(len(user_frame), dtype=bool)
        for segment_value, metric_overrides in segment_map.items():
            override = metric_overrides.get(metric_name)
            if override is None:
                continue
            if override.treatment_effect_absolute is not None:
                override_effect = float(override.treatment_effect_absolute)
                if metric_config.treatment_effect_absolute is not None:
                    override_delta = override_effect - base_absolute
                else:
                    override_delta = override_effect
            elif override.treatment_effect_relative is not None:
                override_effect = float(override.treatment_effect_relative)
                if metric_config.treatment_effect_relative is not None:
                    override_delta = override_effect - base_relative
                else:
                    override_delta = override_effect
            else:
                continue

            mask = segment_values == str(segment_value)
            if mask.any():
                segment_delta[mask] = override_delta
                has_override[mask] = True
        effects = effects + segment_delta
        effects[~has_override] = effects[~has_override]

    return effects


def utc_timestamp_range(start: datetime, count: int, span_seconds: int, rng: np.random.Generator) -> pd.Series:
    offsets = rng.integers(0, max(1, span_seconds), size=count, endpoint=False)
    return pd.to_datetime(start + pd.to_timedelta(offsets, unit="s"), utc=True)


def ensure_tzaware(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)

from __future__ import annotations

from core.contracts.metric_contracts import MetricContract

from .._stats import evaluate_practical_threshold as _evaluate_practical_threshold


def evaluate_practical_threshold(
    metric: MetricContract,
    raw_control_mean: float,
    standard_error: float,
    alpha: float,
    target_power: float,
    effect: float,
) -> tuple[float, bool, bool, float]:
    return _evaluate_practical_threshold(metric, raw_control_mean, standard_error, alpha, target_power, effect)


from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from core.contracts._common import DecisionAction, MetricDirection, ThresholdInterpretation
from core.contracts.metric_contracts import MetricContract
from core.contracts.policy_contracts import PolicyContract


@dataclass(slots=True)
class BusinessValueResult:
    state: str
    metric_name: str
    expected_value: float
    threshold: float
    analyzed_n: int
    effect: float
    direction: str
    message: str
    terminal_action: DecisionAction | None = None


def _favorable_effect(effect: float, direction: MetricDirection) -> float:
    return effect if direction == MetricDirection.higher_is_better else -effect


def evaluate_business_value(
    primary_row: dict[str, Any],
    *,
    metric: MetricContract,
    policy: PolicyContract,
) -> BusinessValueResult:
    config = policy.business_value_policy
    if config is None or not config.enabled:
        return BusinessValueResult(
            state="disabled",
            metric_name=metric.metric_name,
            expected_value=0.0,
            threshold=0.0,
            analyzed_n=int(primary_row.get("analyzed_n", 0) or 0),
            effect=float(primary_row.get("effect", 0.0) or 0.0),
            direction=metric.direction.value,
            message="business_value_disabled",
        )

    analyzed_n = int(primary_row.get("analyzed_n", 0) or 0)
    effect = float(primary_row.get("effect", 0.0) or 0.0)
    threshold_value = float(primary_row.get("practical_threshold_value") or metric.practical_significance_threshold or 0.0)
    favorable_effect = _favorable_effect(effect, metric.direction)
    if config.expected_value_mode.value == "conservative_ci_bound":
        ci_bound = float(primary_row.get("ci_lower") if metric.direction == MetricDirection.higher_is_better else primary_row.get("ci_upper"))
        favorable_effect = _favorable_effect(ci_bound, metric.direction)

    surplus = max(favorable_effect - threshold_value, 0.0)
    expected_value = surplus * max(analyzed_n, 0) * 1000.0
    threshold = float(config.minimum_expected_value_threshold or 0.0)
    if expected_value >= threshold:
        state = "pass"
        message = "expected_value_above_threshold"
        terminal_action = DecisionAction.SHIP_GLOBAL
    else:
        state = "fail"
        message = "expected_value_below_threshold"
        terminal_action = None

    return BusinessValueResult(
        state=state,
        metric_name=metric.metric_name,
        expected_value=expected_value,
        threshold=threshold,
        analyzed_n=analyzed_n,
        effect=effect,
        direction=metric.direction.value,
        message=message,
        terminal_action=terminal_action,
    )


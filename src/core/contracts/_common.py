from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict


class YamlContract(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @classmethod
    def from_yaml_file(cls: type[TContract], path: str | Path) -> TContract:
        return load_contract_from_yaml(path, cls)


TContract = TypeVar("TContract", bound=YamlContract)


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    yaml_path = Path(path)
    with yaml_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if payload is None:
        raise ValueError(f"{yaml_path} is empty")
    if not isinstance(payload, dict):
        raise TypeError(f"{yaml_path} must contain a YAML mapping at the top level")
    return payload


def load_contract_from_yaml(path: str | Path, contract_type: type[TContract]) -> TContract:
    return contract_type.model_validate(load_yaml_mapping(path))


def ensure_utc_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware and expressed in UTC")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field_name} must use UTC (offset +00:00 or Z)")
    return value.astimezone(UTC)


class AnalysisMode(str, Enum):
    fixed_horizon = "fixed_horizon"
    sequential_safe = "sequential_safe"


class PrimaryEstimand(str, Enum):
    itt_assigned = "itt_assigned"
    itt_opportunity = "itt_opportunity"
    tot_exposed = "tot_exposed"


class RandomizationUnit(str, Enum):
    user = "user"


class ComparisonOperator(str, Enum):
    eq = "=="
    ne = "!="
    in_ = "in"
    not_in = "not_in"
    ge = ">="
    gt = ">"
    le = "<="
    lt = "<"


class MetricType(str, Enum):
    binary = "binary"
    continuous = "continuous"
    ratio = "ratio"


class MetricAggregationUnit(str, Enum):
    user = "user"
    user_day = "user_day"


class MetricSourceTable(str, Enum):
    fact_user_outcomes = "fact_user_outcomes"
    fact_user_day = "fact_user_day"


class MetricDirection(str, Enum):
    higher_is_better = "higher_is_better"
    lower_is_better = "lower_is_better"


class NullFillStrategy(str, Enum):
    zero = "zero"
    null = "null"
    drop_row = "drop_row"


class ThresholdInterpretation(str, Enum):
    absolute = "absolute"
    relative = "relative"


class OutlierHandling(str, Enum):
    none = "none"
    winsorize_p99 = "winsorize_p99"
    clip_nonnegative = "clip_nonnegative"


class GuardrailEvaluationMode(str, Enum):
    ci_bound_vs_threshold = "ci_bound_vs_threshold"
    point_estimate_vs_threshold_and_significance = "point_estimate_vs_threshold_and_significance"


class SuccessCriterionMode(str, Enum):
    point_estimate_and_ci_excludes_zero = "point_estimate_and_ci_excludes_zero"
    point_estimate_and_ci_lower_bound_gt_zero = "point_estimate_and_ci_lower_bound_gt_zero"
    ci_lower_bound_gt_practical_threshold = "ci_lower_bound_gt_practical_threshold"
    point_estimate_gt_practical_threshold_only = "point_estimate_gt_practical_threshold_only"


class BusinessValueMode(str, Enum):
    point_estimate = "point_estimate"
    conservative_ci_bound = "conservative_ci_bound"


class SegmentPolicyMode(str, Enum):
    disabled = "disabled"
    pre_registered_segments_only = "pre_registered_segments_only"


class SegmentCorrectionMethod(str, Enum):
    bonferroni = "bonferroni"
    benjamini_hochberg = "benjamini_hochberg"
    none_for_diagnostics_only = "none_for_diagnostics_only"


class SegmentAlphaAllocation(str, Enum):
    inherit_global_alpha = "inherit_global_alpha"
    corrected_from_global_alpha = "corrected_from_global_alpha"


class PolicyStage(str, Enum):
    trust_checks = "trust_checks"
    guardrail_policy = "guardrail_policy"
    primary_success_policy = "primary_success_policy"
    business_value_policy = "business_value_policy"
    segment_policy = "segment_policy"


class DecisionAction(str, Enum):
    INVESTIGATE_INVALID_EXPERIMENT = "INVESTIGATE_INVALID_EXPERIMENT"
    HOLD_GUARDRAIL_RISK = "HOLD_GUARDRAIL_RISK"
    HOLD_INCONCLUSIVE = "HOLD_INCONCLUSIVE"
    RERUN_UNDERPOWERED = "RERUN_UNDERPOWERED"
    SHIP_GLOBAL = "SHIP_GLOBAL"
    SHIP_TARGETED_SEGMENTS = "SHIP_TARGETED_SEGMENTS"


class TruthEffectScale(str, Enum):
    absolute_delta = "absolute_delta"
    relative_lift = "relative_lift"

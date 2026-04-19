from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any


class TrustState(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"


class EvaluabilityState(str, Enum):
    evaluable = "evaluable"
    underpowered = "underpowered"
    insufficient_sample = "insufficient_sample"
    disabled = "disabled"


@dataclass(slots=True)
class SrmCheckResult:
    state: TrustState
    enabled: bool
    p_value: float | None
    chi_square: float | None
    degrees_of_freedom: int | None
    observed_counts: dict[str, int]
    expected_counts: dict[str, float]
    observed_shares: dict[str, float]
    threshold_p_value: float | None
    message: str


@dataclass(slots=True)
class MissingnessCheckResult:
    state: TrustState
    max_missingness_rate: float | None
    overall_missingness_rate: float
    column_missingness_rates: dict[str, float]
    problematic_columns: list[str] = field(default_factory=list)
    message: str = ""


@dataclass(slots=True)
class ExposureSanityResult:
    state: TrustState
    assignments_n: int
    opportunity_users: int
    exposure_users: int
    opportunity_rate: float
    exposure_rate: float
    exposure_to_opportunity_rate: float | None
    inconsistent_exposure_rows: int
    inconsistent_opportunity_rows: int
    message: str


@dataclass(slots=True)
class MetricMaturityResult:
    metric_name: str
    state: TrustState
    maturity_status: str
    total_n: int
    mature_n: int
    immature_n: int
    excluded_n: int
    maturity_window_days: int | None
    message: str


@dataclass(slots=True)
class EvaluabilityResult:
    metric_name: str
    state: TrustState
    status: EvaluabilityState
    total_n: int
    control_n: int
    treatment_n: int
    practical_threshold_value: float | None
    practical_threshold_type: str | None
    mde_at_target_power: float | None
    evaluable: bool
    message: str


@dataclass(slots=True)
class TrustPackResult:
    scenario_id: str
    experiment_id: str
    overall_state: TrustState
    srm: SrmCheckResult
    missingness: MissingnessCheckResult
    exposure_sanity: ExposureSanityResult
    maturity: list[MetricMaturityResult]
    evaluability: list[EvaluabilityResult]
    analysis_summary: list[dict[str, Any]]
    truth_comparison: dict[str, Any]
    notes: list[str] = field(default_factory=list)


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator

from ._common import (
    AnalysisMode,
    DecisionAction,
    MetricDirection,
    PrimaryEstimand,
    RandomizationUnit,
    TruthEffectScale,
    YamlContract,
    ensure_utc_datetime,
)
from .experiment_contracts import FilterDefinition


class AssignmentGroup(str, Enum):
    control = "control"
    treatment = "treatment"


class DeliveryStatus(str, Enum):
    shown = "shown"
    sent = "sent"
    failed = "failed"


class SegmentPolicyModeTable(str, Enum):
    global_only = "global_only"
    pre_registered_segments_only = "pre_registered_segments_only"


class TableContract(YamlContract):
    pass


class DimUsersContract(TableContract):
    user_id: str = Field(min_length=1)
    signup_date: date
    country: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    acquisition_channel: str = Field(min_length=1)
    plan_tier: str = Field(min_length=1)
    tenure_days_at_experiment_start: int
    historical_sessions_28d: float = Field(ge=0)
    historical_revenue_28d: float = Field(ge=0)
    historical_conversion_flag: int = Field(ge=0, le=1)
    historical_retention_score: float = Field(ge=0, le=1)
    device_class: str | None = None
    region: str | None = None
    risk_score_baseline: float | None = None
    engagement_cluster: str | None = None


class DimExperimentsContract(TableContract):
    experiment_id: str = Field(min_length=1)
    experiment_name: str = Field(min_length=1)
    experiment_type: str = Field(min_length=1)
    start_date: date
    end_date: date
    primary_metric: str = Field(min_length=1)
    analysis_mode: AnalysisMode
    primary_estimand: PrimaryEstimand
    target_population_rule: str = Field(min_length=1)
    randomization_unit: RandomizationUnit
    treatment_share_target: float = Field(ge=0, le=1)
    decision_policy_id: str = Field(min_length=1)
    segment_policy_mode: SegmentPolicyModeTable
    pre_registered_groupby_columns: list[str]
    pre_registered_filters: list[FilterDefinition] | None = None
    secondary_metrics: list[str] = Field(default_factory=list)
    guardrail_metrics: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_dim_experiments(self) -> "DimExperimentsContract":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be earlier than end_date")
        if len(set(self.pre_registered_groupby_columns)) != len(self.pre_registered_groupby_columns):
            raise ValueError("pre_registered_groupby_columns must be unique")
        return self


class FactAssignmentsContract(TableContract):
    experiment_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    assignment_ts: datetime
    assigned_group: AssignmentGroup
    assignment_bucket: int | str
    is_eligible: int = Field(ge=0, le=1)
    assignment_reason: str | None = None

    @model_validator(mode="after")
    def _validate_assignment_ts(self) -> "FactAssignmentsContract":
        self.assignment_ts = ensure_utc_datetime(self.assignment_ts, "assignment_ts")
        return self


class FactOpportunitiesContract(TableContract):
    experiment_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    opportunity_ts: datetime
    surface: str = Field(min_length=1)
    opportunity_count: int = Field(ge=0)
    first_opportunity_flag: int = Field(ge=0, le=1)
    opportunity_source: str | None = None

    @model_validator(mode="after")
    def _validate_opportunity_ts(self) -> "FactOpportunitiesContract":
        self.opportunity_ts = ensure_utc_datetime(self.opportunity_ts, "opportunity_ts")
        return self


class FactExposuresContract(TableContract):
    experiment_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    opportunity_ts: datetime
    exposure_ts: datetime
    assigned_group: AssignmentGroup
    variant_served: AssignmentGroup
    delivery_status: DeliveryStatus
    exposure_count: int = Field(ge=0)
    first_exposure_flag: int = Field(ge=0, le=1)
    surface: str | None = None

    @model_validator(mode="after")
    def _validate_exposure_timestamps(self) -> "FactExposuresContract":
        self.opportunity_ts = ensure_utc_datetime(self.opportunity_ts, "opportunity_ts")
        self.exposure_ts = ensure_utc_datetime(self.exposure_ts, "exposure_ts")
        if self.exposure_ts < self.opportunity_ts:
            raise ValueError("exposure_ts must be on or after opportunity_ts")
        return self


class FactUserDayContract(TableContract):
    date: date
    experiment_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    assigned_group: AssignmentGroup
    had_opportunity: int = Field(ge=0, le=1)
    is_exposed: int = Field(ge=0, le=1)
    sessions: int = Field(ge=0)
    days_active: int = Field(ge=0)
    revenue: float = Field(ge=0)
    converted: int = Field(ge=0, le=1)
    retained_d1_flag: int = Field(ge=0, le=1)
    retained_d7_flag: int = Field(ge=0, le=1)
    notif_clicked: int = Field(ge=0, le=1)
    guardrail_uninstall_flag: int = Field(ge=0, le=1)
    guardrail_support_ticket_flag: int = Field(ge=0, le=1)
    content_consumption_minutes: float | None = Field(default=None, ge=0)
    refund_flag: int | None = Field(default=None, ge=0, le=1)
    latency_complaint_flag: int | None = Field(default=None, ge=0, le=1)


class FactUserOutcomesContract(TableContract):
    experiment_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    assigned_group: AssignmentGroup
    had_opportunity: int = Field(ge=0, le=1)
    is_exposed: int = Field(ge=0, le=1)
    first_opportunity_ts: datetime | None = None
    first_exposure_ts: datetime | None = None
    days_since_first_opportunity: int = Field(ge=0)
    analysis_window_days: int = Field(gt=0)
    primary_outcome_value: float
    primary_outcome_name: str = Field(min_length=1)
    conversions_7d: int = Field(ge=0)
    sessions_7d: int = Field(ge=0)
    sessions_30d: int = Field(ge=0)
    impressions_7d: int = Field(ge=0)
    clicks_7d: int = Field(ge=0)
    retention_7d: int = Field(ge=0, le=1)
    retention_30d: int = Field(ge=0, le=1)
    revenue_30d: float = Field(ge=0)
    engagement_7d: float = Field(ge=0)
    guardrail_1_value: float | None = None
    guardrail_2_value: float | None = None
    support_tickets_7d: int | None = Field(default=None, ge=0)
    uninstalls_7d: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_outcome_timestamps(self) -> "FactUserOutcomesContract":
        if self.first_opportunity_ts is not None:
            self.first_opportunity_ts = ensure_utc_datetime(self.first_opportunity_ts, "first_opportunity_ts")
        if self.first_exposure_ts is not None:
            self.first_exposure_ts = ensure_utc_datetime(self.first_exposure_ts, "first_exposure_ts")
        return self


class FactValidationTruthContract(TableContract):
    scenario_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    primary_metric_name: str = Field(min_length=1)
    true_primary_effect_value: float
    true_primary_effect_scale: TruthEffectScale
    primary_metric_direction: MetricDirection
    true_effect_by_segment_json: dict[str, Any] | str
    true_guardrail_impact_json: dict[str, Any] | str
    expected_srm_flag: int = Field(ge=0, le=1)
    expected_missing_exposure_pattern: str = Field(min_length=1)
    expected_peeking_risk: str = Field(min_length=1)
    expected_recommendation: DecisionAction


class FactBenchmarkObservationsContract(TableContract):
    benchmark_dataset: str = Field(min_length=1)
    observation_id: str = Field(min_length=1)
    assigned_group: AssignmentGroup
    treatment_flag: int = Field(ge=0, le=1)
    primary_outcome_value: float
    secondary_outcome_value: float | None = None
    feature_vector_ref: str = Field(min_length=1)


CANONICAL_TABLE_MODELS: dict[str, type[TableContract]] = {
    "dim_users": DimUsersContract,
    "dim_experiments": DimExperimentsContract,
    "fact_assignments": FactAssignmentsContract,
    "fact_opportunities": FactOpportunitiesContract,
    "fact_exposures": FactExposuresContract,
    "fact_user_day": FactUserDayContract,
    "fact_user_outcomes": FactUserOutcomesContract,
    "fact_validation_truth": FactValidationTruthContract,
    "fact_benchmark_observations": FactBenchmarkObservationsContract,
}

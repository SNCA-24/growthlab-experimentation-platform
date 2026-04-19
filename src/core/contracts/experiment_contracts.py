from __future__ import annotations

from datetime import datetime
from math import isclose
from typing import Any

from pydantic import Field, model_validator

from ._common import AnalysisMode, ComparisonOperator, PrimaryEstimand, RandomizationUnit, YamlContract, ensure_utc_datetime


class FilterDefinition(YamlContract):
    column: str = Field(min_length=1)
    op: ComparisonOperator
    value: Any | None = None
    values: list[Any] | None = None

    @model_validator(mode="after")
    def _validate_payload(self) -> "FilterDefinition":
        if self.op in {ComparisonOperator.in_, ComparisonOperator.not_in}:
            if self.values is None:
                raise ValueError(f"{self.op.value} filters require values")
            if not self.values:
                raise ValueError(f"{self.op.value} filters require at least one value")
            if self.value is not None:
                raise ValueError(f"{self.op.value} filters must not set value")
        else:
            if self.value is None:
                raise ValueError(f"{self.op.value} filters require value")
            if self.values is not None:
                raise ValueError(f"{self.op.value} filters must not set values")
        return self


class VariantDefinition(YamlContract):
    name: str = Field(min_length=1)
    weight: float = Field(ge=0)
    description: str | None = None
    is_control: bool = False


class ExperimentContract(YamlContract):
    experiment_id: str = Field(min_length=1)
    experiment_name: str = Field(min_length=1)
    experiment_type: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    assignment_start_ts_utc: datetime
    assignment_end_ts_utc: datetime
    observation_end_ts_utc: datetime
    analysis_mode: AnalysisMode
    primary_estimand: PrimaryEstimand
    randomization_unit: RandomizationUnit
    variants: list[VariantDefinition]
    target_population_filters: list[FilterDefinition]
    primary_metric: str = Field(min_length=1)
    decision_policy_id: str = Field(min_length=1)
    description: str | None = None
    secondary_metrics: list[str] = Field(default_factory=list)
    guardrail_metrics: list[str] = Field(default_factory=list)
    diagnostic_metrics: list[str] = Field(default_factory=list)
    pre_registered_groupby_columns: list[str] = Field(default_factory=list)
    pre_registered_filters: list[FilterDefinition] = Field(default_factory=list)
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_experiment_contract(self) -> "ExperimentContract":
        self.assignment_start_ts_utc = ensure_utc_datetime(self.assignment_start_ts_utc, "assignment_start_ts_utc")
        self.assignment_end_ts_utc = ensure_utc_datetime(self.assignment_end_ts_utc, "assignment_end_ts_utc")
        self.observation_end_ts_utc = ensure_utc_datetime(self.observation_end_ts_utc, "observation_end_ts_utc")

        if self.assignment_start_ts_utc >= self.assignment_end_ts_utc:
            raise ValueError("assignment_start_ts_utc must be earlier than assignment_end_ts_utc")
        if self.assignment_end_ts_utc > self.observation_end_ts_utc:
            raise ValueError("assignment_end_ts_utc must be less than or equal to observation_end_ts_utc")

        if len(self.variants) < 2:
            raise ValueError("at least two variants are required")

        variant_names = [variant.name for variant in self.variants]
        if len(set(variant_names)) != len(variant_names):
            raise ValueError("variant names must be unique")

        control_variants = [variant for variant in self.variants if variant.is_control]
        if len(control_variants) != 1:
            raise ValueError("exactly one variant must declare is_control: true")

        total_weight = sum(variant.weight for variant in self.variants)
        if not isclose(total_weight, 1.0, abs_tol=1e-6):
            raise ValueError("variant weights must sum to 1.0")

        if any(variant.weight < 0 for variant in self.variants):
            raise ValueError("variant weights must be non-negative")

        metric_ids = [self.primary_metric, *self.secondary_metrics, *self.guardrail_metrics, *self.diagnostic_metrics]
        if len(set(metric_ids)) != len(metric_ids):
            raise ValueError("primary, secondary, guardrail, and diagnostic metric IDs must be unique")

        if len(set(self.pre_registered_groupby_columns)) != len(self.pre_registered_groupby_columns):
            raise ValueError("pre_registered_groupby_columns must be unique")

        if any(not column for column in self.pre_registered_groupby_columns):
            raise ValueError("pre_registered_groupby_columns must not contain empty values")

        if any(not tag for tag in self.tags):
            raise ValueError("tags must not contain empty values")

        return self

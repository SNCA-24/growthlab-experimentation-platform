from __future__ import annotations

from pydantic import Field, model_validator

from ._common import (
    MetricAggregationUnit,
    MetricDirection,
    MetricSourceTable,
    MetricType,
    NullFillStrategy,
    OutlierHandling,
    ThresholdInterpretation,
    YamlContract,
)


class MetricContract(YamlContract):
    metric_name: str = Field(min_length=1)
    metric_label: str = Field(min_length=1)
    metric_type: MetricType
    source_table: MetricSourceTable
    aggregation_unit: MetricAggregationUnit
    window_days: int = Field(gt=0)
    direction: MetricDirection
    practical_significance_threshold: float
    description: str | None = None
    metric_column: str | None = None
    covariate_column: str | None = None
    numerator_column: str | None = None
    denominator_column: str | None = None
    allowed_degradation_threshold: float | None = None
    practical_significance_threshold_type: ThresholdInterpretation | None = None
    allowed_degradation_threshold_type: ThresholdInterpretation | None = None
    maturity_window_days: int | None = Field(default=None, ge=0)
    null_fill_strategy: NullFillStrategy | None = None
    winsorization: str | None = None
    outlier_handling: OutlierHandling | None = None
    segment_eligible: bool = False
    policy_weight: float | None = Field(default=None, ge=0)
    owner: str | None = None

    @model_validator(mode="after")
    def _validate_metric_contract(self) -> "MetricContract":
        if self.metric_type == MetricType.ratio:
            if self.numerator_column is None or self.denominator_column is None:
                raise ValueError("ratio metrics require numerator_column and denominator_column")
            if "null_fill_strategy" not in self.model_fields_set:
                raise ValueError("ratio metrics must declare null_fill_strategy")
        else:
            if self.metric_column is None:
                raise ValueError("non-ratio metrics require metric_column")
            if self.numerator_column is not None or self.denominator_column is not None:
                raise ValueError("non-ratio metrics must not set numerator_column or denominator_column")

        if "practical_significance_threshold_type" not in self.model_fields_set or self.practical_significance_threshold_type is None:
            raise ValueError("practical_significance_threshold_type is required")

        if self.allowed_degradation_threshold is not None and self.allowed_degradation_threshold_type is None:
            raise ValueError("allowed_degradation_threshold_type is required when allowed_degradation_threshold is set")

        if self.metric_name == "":
            raise ValueError("metric_name must not be empty")

        if self.window_days <= 0:
            raise ValueError("window_days must be positive")

        if self.maturity_window_days is not None and self.maturity_window_days < 0:
            raise ValueError("maturity_window_days must be non-negative")

        return self


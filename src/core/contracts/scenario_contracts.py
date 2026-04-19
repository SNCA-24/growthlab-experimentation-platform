from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from ._common import DecisionAction, MetricDirection, TruthEffectScale, YamlContract, ensure_utc_datetime
from .experiment_contracts import ExperimentContract


class ScenarioType(str, Enum):
    aa_null = "aa_null"
    global_positive = "global_positive"
    guardrail_harm = "guardrail_harm"
    delayed_effect = "delayed_effect"
    segment_only_win = "segment_only_win"
    srm_invalid = "srm_invalid"
    low_power_noisy = "low_power_noisy"


class DistributionType(str, Enum):
    lognormal = "lognormal"
    zero_inflated_lognormal = "zero_inflated_lognormal"
    bernoulli = "bernoulli"
    beta = "beta"


class TenureDistributionType(str, Enum):
    truncated_exponential = "truncated_exponential"


class DistributionSpec(YamlContract):
    distribution: DistributionType | None = None
    mean: float | None = None
    sigma: float | None = None
    zero_rate: float | None = Field(default=None, ge=0, le=1)
    bernoulli_p: float | None = Field(default=None, ge=0, le=1)
    alpha: float | None = Field(default=None, gt=0)
    beta: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _validate_distribution_spec(self) -> "DistributionSpec":
        if self.distribution == DistributionType.lognormal:
            if self.mean is None or self.sigma is None:
                raise ValueError("lognormal distributions require mean and sigma")
        elif self.distribution == DistributionType.zero_inflated_lognormal:
            if self.mean is None or self.sigma is None or self.zero_rate is None:
                raise ValueError("zero_inflated_lognormal distributions require mean, sigma, and zero_rate")
        elif self.distribution == DistributionType.bernoulli:
            if self.bernoulli_p is None:
                raise ValueError("bernoulli distributions require bernoulli_p")
        elif self.distribution == DistributionType.beta:
            if self.alpha is None or self.beta is None:
                raise ValueError("beta distributions require alpha and beta")
        elif self.distribution is None:
            if all(
                value is None
                for value in (self.mean, self.sigma, self.zero_rate, self.bernoulli_p, self.alpha, self.beta)
            ):
                raise ValueError("distribution specs require either distribution metadata or parameter values")
        return self


class TenureDaysDistribution(YamlContract):
    distribution_type: TenureDistributionType = Field(alias="type")
    max_days: int = Field(gt=0)


class PopulationConfig(YamlContract):
    n_users: int = Field(gt=0)
    country_distribution: dict[str, float]
    platform_distribution: dict[str, float]
    acquisition_channel_distribution: dict[str, float]
    plan_tier_distribution: dict[str, float]
    tenure_days_distribution: TenureDaysDistribution
    pre_registered_group_mix: dict[str, dict[str, float]] | None = None


class BaselineBehaviorConfig(YamlContract):
    historical_sessions_28d: DistributionSpec
    historical_revenue_28d: DistributionSpec
    historical_conversion_flag: DistributionSpec
    historical_retention_score: DistributionSpec


class OpportunityAndDeliveryConfig(YamlContract):
    trigger_probability: float = Field(ge=0, le=1)
    delivery_probability_control: float = Field(ge=0, le=1)
    delivery_probability_treatment: float = Field(ge=0, le=1)
    exposure_surface: str = Field(min_length=1)


class MetricSignalConfig(YamlContract):
    baseline_rate: float | None = Field(default=None, ge=0)
    baseline_mean: float | None = None
    baseline_std: float | None = Field(default=None, ge=0)
    treatment_effect_absolute: float | None = None
    treatment_effect_relative: float | None = None
    winsorize_reference: str | None = None
    delayed_effect_curve: dict[str, float] | None = None


class DataQualityAndNoiseConfig(YamlContract):
    missingness_rate: float = Field(ge=0, le=1)
    duplicate_user_rate: float = Field(ge=0, le=1)
    event_underlogging_rate: float = Field(ge=0, le=1)
    outlier_revenue_rate: float = Field(ge=0, le=1)
    outlier_revenue_multiplier: float = Field(gt=0)


class PathologyFlagsConfig(YamlContract):
    inject_srm: bool
    srm_target_shares: dict[str, float] | None = None
    inject_treatment_leakage: bool
    inject_exposure_asymmetry: bool
    inject_peeking_checkpoints: bool
    peeking_checkpoints: list[datetime] | None = None

    @model_validator(mode="after")
    def _validate_pathology_flags(self) -> "PathologyFlagsConfig":
        if self.inject_srm:
            if self.srm_target_shares is None or not self.srm_target_shares:
                raise ValueError("inject_srm requires srm_target_shares")
            if abs(sum(self.srm_target_shares.values()) - 1.0) > 1e-6:
                raise ValueError("srm_target_shares must sum to 1.0")
        if self.peeking_checkpoints is not None:
            self.peeking_checkpoints = [ensure_utc_datetime(item, "peeking_checkpoints") for item in self.peeking_checkpoints]
        return self


class ValidationTruthContract(YamlContract):
    scenario_id: str | None = Field(default=None, min_length=1)
    experiment_id: str | None = Field(default=None, min_length=1)
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


class ScenarioContract(YamlContract):
    schema_version: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    scenario_name: str = Field(min_length=1)
    scenario_type: ScenarioType
    description: str | None = None
    random_seed: int = Field(ge=0)
    experiment: ExperimentContract
    population: PopulationConfig
    baseline_behavior: BaselineBehaviorConfig
    opportunity_and_delivery: OpportunityAndDeliveryConfig
    metric_generation: dict[str, MetricSignalConfig]
    segment_effect_overrides: dict[str, dict[str, dict[str, MetricSignalConfig]]] = Field(default_factory=dict)
    data_quality_and_noise: DataQualityAndNoiseConfig
    pathology_flags: PathologyFlagsConfig
    validation_truth: ValidationTruthContract

    @model_validator(mode="after")
    def _validate_scenario_contract(self) -> "ScenarioContract":
        if self.validation_truth.scenario_id is not None and self.scenario_id != self.validation_truth.scenario_id:
            raise ValueError("scenario_id must match validation_truth.scenario_id")
        if self.validation_truth.experiment_id is not None and self.experiment.experiment_id != self.validation_truth.experiment_id:
            raise ValueError("experiment.experiment_id must match validation_truth.experiment_id")
        if self.experiment.primary_metric != self.validation_truth.primary_metric_name:
            raise ValueError("experiment.primary_metric must match validation_truth.primary_metric_name")
        if self.experiment.primary_metric not in self.metric_generation:
            raise ValueError("metric_generation must include the primary metric")

        for segment_dimension, segment_overrides in self.segment_effect_overrides.items():
            for segment_value, metric_overrides in segment_overrides.items():
                missing_override_ids = sorted({metric_id for metric_id in metric_overrides if metric_id not in self.metric_generation})
                if missing_override_ids:
                    raise ValueError(
                        f"segment_effect_overrides[{segment_dimension}][{segment_value}] references unknown metric(s): "
                        f"{', '.join(missing_override_ids)}"
                    )
        return self

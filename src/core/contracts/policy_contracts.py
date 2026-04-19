from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from ._common import (
    BusinessValueMode,
    DecisionAction,
    GuardrailEvaluationMode,
    PolicyStage,
    SegmentAlphaAllocation,
    SegmentCorrectionMethod,
    SegmentPolicyMode,
    SuccessCriterionMode,
    ThresholdInterpretation,
    YamlContract,
)


class SrmCheckConfig(YamlContract):
    enabled: bool
    threshold_p_value: float = Field(gt=0, lt=1)


class TrustChecksConfig(YamlContract):
    enabled: bool
    srm_check: SrmCheckConfig
    min_total_sample_size: int = Field(gt=0)
    require_metric_maturity: bool
    max_missingness_rate: float = Field(ge=0, le=1)
    require_exposure_opportunity_sanity: bool
    min_group_sample_size: int | None = Field(default=None, gt=0)
    min_sample_for_practical_significance: bool | None = None
    practical_significance_power_target: float | None = Field(default=None, gt=0, lt=1)
    fail_action_on_srm: DecisionAction | None = None
    fail_action_on_maturity: DecisionAction | None = None
    fail_action_on_missingness: DecisionAction | None = None


class GuardrailPolicyConfig(YamlContract):
    enabled: bool
    guardrail_evaluation_mode: GuardrailEvaluationMode
    guardrail_fail_if_any_fail: bool
    guardrail_metric_overrides: dict[str, Any] | None = None
    max_guardrail_failures_allowed: int | None = Field(default=None, ge=0)
    require_all_pre_registered_segments_to_pass: bool | None = None


class PrimarySuccessPolicyConfig(YamlContract):
    enabled: bool
    success_criterion_mode: SuccessCriterionMode
    require_statistical_significance: bool
    require_practical_significance: bool
    require_business_value_positive: bool
    primary_metric_alpha_override: float | None = Field(default=None, gt=0, lt=1)
    practical_significance_override: float | None = None
    minimum_effect_direction_consistency: bool | None = None


class BusinessValuePolicyConfig(YamlContract):
    enabled: bool
    expected_value_mode: BusinessValueMode | None = None
    minimum_expected_value_threshold: float | None = None
    cost_model_ref: str | None = None
    audience_size_source: str | None = None
    value_scale: str | None = None

    @model_validator(mode="after")
    def _validate_business_value_policy(self) -> "BusinessValuePolicyConfig":
        if self.enabled:
            if self.expected_value_mode is None:
                raise ValueError("enabled business_value_policy requires expected_value_mode")
            if self.minimum_expected_value_threshold is None:
                raise ValueError("enabled business_value_policy requires minimum_expected_value_threshold")
        return self


class SegmentPolicyConfig(YamlContract):
    enabled: bool
    segment_policy_mode: SegmentPolicyMode | None = None
    segment_correction_method: SegmentCorrectionMethod | None = None
    segment_alpha_allocation: SegmentAlphaAllocation | None = None
    require_interaction_evidence: bool | None = None
    interaction_p_value_threshold: float | None = Field(default=None, gt=0, lt=1)
    require_segment_guardrail_pass: bool | None = None
    min_segment_sample_size: int | None = Field(default=None, gt=0)
    max_segments_evaluated: int | None = Field(default=None, gt=0)
    allow_targeted_rollout_if_global_fails: bool | None = None
    segment_success_criterion_mode: SuccessCriterionMode | None = None

    @model_validator(mode="after")
    def _validate_segment_policy(self) -> "SegmentPolicyConfig":
        if self.enabled:
            missing_fields = [
                field_name
                for field_name, field_value in {
                    "segment_policy_mode": self.segment_policy_mode,
                    "segment_correction_method": self.segment_correction_method,
                    "segment_alpha_allocation": self.segment_alpha_allocation,
                    "require_interaction_evidence": self.require_interaction_evidence,
                    "interaction_p_value_threshold": self.interaction_p_value_threshold,
                    "require_segment_guardrail_pass": self.require_segment_guardrail_pass,
                    "min_segment_sample_size": self.min_segment_sample_size,
                }.items()
                if field_value is None
            ]
            if missing_fields:
                raise ValueError(f"enabled segment_policy requires fields: {', '.join(missing_fields)}")
            if self.segment_policy_mode != SegmentPolicyMode.pre_registered_segments_only:
                raise ValueError("enabled segment policy must use pre_registered_segments_only mode")
            if self.segment_correction_method == SegmentCorrectionMethod.none_for_diagnostics_only:
                raise ValueError("none_for_diagnostics_only is not allowed for rollout-affecting segment policy")
        elif self.segment_policy_mode not in (None, SegmentPolicyMode.disabled):
            raise ValueError("disabled segment policy must use disabled mode")
        return self


class PolicyContract(YamlContract):
    policy_id: str = Field(min_length=1)
    policy_name: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    default_alpha: float = Field(gt=0, lt=1)
    confidence_level: float = Field(gt=0, lt=1)
    execution_order: list[PolicyStage]
    trust_checks: TrustChecksConfig
    guardrail_policy: GuardrailPolicyConfig
    primary_success_policy: PrimarySuccessPolicyConfig
    segment_policy: SegmentPolicyConfig | None = None
    business_value_policy: BusinessValuePolicyConfig | None = None
    notes: str | None = None
    owner: str | None = None

    @model_validator(mode="after")
    def _validate_policy_contract(self) -> "PolicyContract":
        if len(self.execution_order) != len(set(self.execution_order)):
            raise ValueError("execution_order must not contain duplicate stages")

        required_prefix = [
            PolicyStage.trust_checks,
            PolicyStage.guardrail_policy,
            PolicyStage.primary_success_policy,
        ]
        if self.execution_order[:3] != required_prefix:
            raise ValueError("execution_order must begin with trust_checks, guardrail_policy, and primary_success_policy")

        if self.business_value_policy is not None and self.business_value_policy.enabled:
            if PolicyStage.business_value_policy not in self.execution_order:
                raise ValueError("enabled business_value_policy must appear in execution_order")

        if self.segment_policy is not None and self.segment_policy.enabled:
            if PolicyStage.segment_policy not in self.execution_order:
                raise ValueError("enabled segment_policy must appear in execution_order")

        if PolicyStage.business_value_policy in self.execution_order and PolicyStage.segment_policy in self.execution_order:
            if self.execution_order.index(PolicyStage.business_value_policy) > self.execution_order.index(PolicyStage.segment_policy):
                raise ValueError("business_value_policy must execute before segment_policy")

        return self


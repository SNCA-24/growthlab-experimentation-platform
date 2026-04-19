# GrowthLab — Policy Engine Config Schema
## Version
**v0.3**

## Purpose
This document defines the **config-driven policy engine schema** for GrowthLab.

The policy engine is responsible for converting experiment analysis outputs into deterministic decisions such as:
- `INVESTIGATE_INVALID_EXPERIMENT`
- `HOLD_GUARDRAIL_RISK`
- `HOLD_INCONCLUSIVE`
- `SHIP_GLOBAL`
- `SHIP_TARGETED_SEGMENTS`

This schema is the source of truth for:
- trust checks
- confidence level / alpha
- practical significance interpretation
- CI-vs-point-estimate decision strictness
- evaluability against practical thresholds
- guardrail protection logic
- segment rollout correction rules
- execution order and short-circuit behavior

---

# 1. Design principles

## P1. Deterministic and config-driven
The policy engine must not rely on hidden `if/else` logic in notebooks or scripts.

## P2. Sequential execution with short-circuiting
The policy engine must evaluate rules in a fixed hierarchy.  
If an upstream trust check fails, downstream business decisions must not run.

## P3. Trust before optimization
If the experiment is invalid, no primary-metric “win” matters.

## P4. Guardrails before launch
A harmful experiment should not ship even if the primary metric looks strong.

## P5. Confidence semantics must be explicit
The policy engine must know whether success is judged by:
- point estimate,
- CI lower bound,
- CI exclusion of zero,
- or a combined rule.

## P6. Segment rollout must be multiplicity-aware
Any segment-level rollout decision in v1 must use a declared multiple-testing correction method.

## P7. Diagnostics and rollout decisions are different
Some analysis may be shown diagnostically in the UI without being eligible to drive rollout.

---

# 2. Policy output actions

## Allowed final actions
- `INVESTIGATE_INVALID_EXPERIMENT`
- `HOLD_GUARDRAIL_RISK`
- `HOLD_INCONCLUSIVE`
- `RERUN_UNDERPOWERED`
- `SHIP_GLOBAL`
- `SHIP_TARGETED_SEGMENTS`

## Meaning
### `INVESTIGATE_INVALID_EXPERIMENT`
Used when trust checks fail. Example:
- SRM
- invalid exposure pattern
- severe missingness
- unmatured metric windows

### `HOLD_GUARDRAIL_RISK`
Used when trust checks pass, but one or more guardrails fail.

### `HOLD_INCONCLUSIVE`
Used when the experiment is valid, but evidence is insufficient to ship.

### `RERUN_UNDERPOWERED`
Used when the experiment is valid but clearly underpowered or too immature for a final decision.

### `SHIP_GLOBAL`
Used when the experiment passes trust checks, guardrails, and primary success criteria globally.

### `SHIP_TARGETED_SEGMENTS`
Used only when:
- segment policy mode allows it
- segments are pre-registered
- multiplicity correction is applied
- segment-specific criteria pass

---

# 3. Execution hierarchy

The engine must evaluate in this order.

## Level 1 — Trust checks
Examples:
- SRM checks
- minimum sample size
- minimum power adequacy
- metric maturity
- exposure/opportunity sanity
- missingness thresholds
- sequential/fixed-horizon compatibility

### If fail
Return:
- `INVESTIGATE_INVALID_EXPERIMENT`
or
- `RERUN_UNDERPOWERED`
depending on failure type

## Level 2 — Do no harm
Examples:
- guardrail degradation checks
- catastrophic secondary metric failures
- policy-defined risk flags

### If fail
Return:
- `HOLD_GUARDRAIL_RISK`

## Level 3 — Primary success
Examples:
- statistical significance check
- practical significance check

### If fail globally
Proceed to Level 5 only if segment policy is allowed and configured to evaluate fallback segment shipping.

### If pass globally
Proceed to Level 4 if business-value gating is enabled, otherwise:
- continue to segment-safety checks only if configured under guardrail policy
- else return `SHIP_GLOBAL`

## Level 4 — Business value
Examples:
- expected value / business value check
- minimum rollout value threshold
- value-risk tradeoff checks

### If fail
Return:
- `HOLD_INCONCLUSIVE`

### If pass
- continue to segment-safety checks only if configured under guardrail policy
- else return `SHIP_GLOBAL`

## Level 5 — Pre-registered segment rollout
Examples:
- corrected segment-level statistical check
- segment-level practical significance
- segment-level guardrail safety
- segment-level minimum sample / power
- interaction-effect or equivalent divergence evidence

### If one or more eligible segments pass
Return:
- `SHIP_TARGETED_SEGMENTS`

### Else
Return:
- `HOLD_INCONCLUSIVE`

---

# 4. Top-level schema

Each policy should be defined as a YAML object.

## Required top-level fields
- `policy_id`
- `policy_name`
- `policy_version`
- `default_alpha`
- `confidence_level`
- `execution_order`
- `trust_checks`
- `guardrail_policy`
- `primary_success_policy`

## Optional top-level fields
- `segment_policy`
- `business_value_policy`
- `notes`
- `owner`

---

# 5. Field definitions

## 5.1 Identity fields

### `policy_id`
Unique machine-readable ID.

**Type:** string  
**Example:** `growth_default_v1`

### `policy_name`
Human-readable name.

**Type:** string

### `policy_version`
Semantic or explicit version tag.

**Type:** string  
**Example:** `v1`

---

## 5.2 Global statistical fields

### `default_alpha`
Default significance level.

**Type:** float  
**Example:** `0.05`

### `confidence_level`
Confidence interval level.

**Type:** float  
**Example:** `0.95`

### Invariant
- `confidence_level = 1 - default_alpha` is recommended for v1 unless explicitly overridden

---

## 5.3 Execution-order field

### `execution_order`
Defines the policy stages in order.

**Type:** ordered list  
**Expected v1 value:**
```yaml
execution_order:
  - trust_checks
  - guardrail_policy
  - primary_success_policy
  - business_value_policy
  - segment_policy
```

### Invariant
- execution order must short-circuit on terminal failure
- if `business_value_policy.enabled == true`, it must appear in `execution_order` or be explicitly documented as nested inside `primary_success_policy`

---

# 6. Trust checks schema

## Required fields
- `enabled`
- `srm_check`
- `min_total_sample_size`
- `require_metric_maturity`
- `max_missingness_rate`
- `require_exposure_opportunity_sanity`

## Optional fields
- `min_group_sample_size`
- `min_sample_for_practical_significance`
- `practical_significance_power_target`
- `fail_action_on_srm`
- `fail_action_on_maturity`
- `fail_action_on_missingness`

## Example semantics
### `srm_check`
```yaml
srm_check:
  enabled: true
  threshold_p_value: 0.001
```

### `min_total_sample_size`
Minimum total analyzable rows.

### `min_sample_for_practical_significance`
If set, the engine must check whether the experiment has enough analyzable sample to detect the configured practical significance threshold at the target power level.

This is **not** post-hoc observed power.

### `practical_significance_power_target`
Target power used for evaluability checks against the practical threshold.

**Recommended v1 default:** `0.80`

### `require_metric_maturity`
If true, metrics must satisfy maturity rules before final policy decisions.

### `require_exposure_opportunity_sanity`
If true, trust checks fail when opportunity/exposure behavior suggests instrumentation problems.

---

# 7. Guardrail policy schema

## Required fields
- `enabled`
- `guardrail_evaluation_mode`
- `guardrail_fail_if_any_fail`

## Optional fields
- `guardrail_metric_overrides`
- `max_guardrail_failures_allowed`
- `require_all_pre_registered_segments_to_pass`

## `guardrail_evaluation_mode`
Defines how guardrail harm is judged.

**Type:** enum  
**Allowed v1 values:**
- `ci_bound_vs_threshold`
- `point_estimate_vs_threshold_and_significance`

## Recommended v1 default
- `ci_bound_vs_threshold`

### Why
This is stricter and safer for enterprise-style launch gating.

## Guardrail decision rule
Guardrails should use **non-inferiority-style logic**.

The engine must read the metric direction from the metric schema and compare the **worst-case confidence bound** against the allowed degradation threshold:
- if `direction == lower_is_better`, check the **upper** confidence bound for harmful increase
- if `direction == higher_is_better`, check the **lower** confidence bound for harmful decrease

For v1, the recommended interpretation is:
- if the worst-case bound exceeds the allowed degradation threshold in the harmful direction, hold the experiment

## Optional segment-safety mode
If `require_all_pre_registered_segments_to_pass == true`, then before any `SHIP_GLOBAL` action is allowed, the engine must loop through all pre-registered segments and ensure guardrails also pass at the segment level.

This is a stricter anti-Simpson’s-paradox safety mode and should be configurable rather than forced universally.

---

# 8. Primary success policy schema

## Required fields
- `enabled`
- `success_criterion_mode`
- `require_statistical_significance`
- `require_practical_significance`
- `require_business_value_positive`

## Optional fields
- `primary_metric_alpha_override`
- `practical_significance_override`
- `minimum_effect_direction_consistency`

## `success_criterion_mode`
Defines how confidence intervals and point estimates are used.

**Type:** enum  
**Allowed v1 values:**
- `point_estimate_and_ci_excludes_zero`
- `point_estimate_and_ci_lower_bound_gt_zero`
- `ci_lower_bound_gt_practical_threshold`
- `point_estimate_gt_practical_threshold_only`

## Recommended v1 default
- `point_estimate_and_ci_excludes_zero` for general use
- `ci_lower_bound_gt_practical_threshold` for stricter launch decisions

## Interpretation
### `point_estimate_and_ci_excludes_zero`
Requires:
- observed effect clears practical threshold
- CI excludes zero in the favorable direction

### `point_estimate_and_ci_lower_bound_gt_zero`
Requires:
- observed effect clears practical threshold
- CI lower bound is above zero

### `ci_lower_bound_gt_practical_threshold`
Strictest version. Requires:
- lower confidence bound itself clears the practical significance threshold

### `point_estimate_gt_practical_threshold_only`
Allowed only for diagnostics, not recommended for final ship decisions

---

# 9. Business value policy schema

## Optional but recommended in v1

### Required fields if enabled
- `enabled`
- `expected_value_mode`
- `minimum_expected_value_threshold`

### Optional fields
- `cost_model_ref`
- `audience_size_source`
- `value_scale`

## `expected_value_mode`
**Type:** enum  
**Allowed values:**
- `point_estimate`
- `conservative_ci_bound`

## Recommended v1 default
- `point_estimate` for first implementation
- optionally `conservative_ci_bound` later if you want stricter shipping logic

---

# 10. Segment policy schema

## Required fields if enabled
- `enabled`
- `segment_policy_mode`
- `segment_correction_method`
- `segment_alpha_allocation`
- `require_interaction_evidence`
- `interaction_p_value_threshold`
- `require_segment_guardrail_pass`
- `min_segment_sample_size`

## Optional fields
- `max_segments_evaluated`
- `allow_targeted_rollout_if_global_fails`
- `segment_success_criterion_mode`

## `segment_policy_mode`
**Type:** enum  
**Allowed values:**
- `disabled`
- `pre_registered_segments_only`

## `segment_correction_method`
**Type:** enum  
**Allowed values:**
- `bonferroni`
- `benjamini_hochberg`
- `none_for_diagnostics_only`

### Strong v1 rule
For rollout-affecting segment decisions:
- `none_for_diagnostics_only` must not be accepted as a shipping policy

## `segment_alpha_allocation`
Defines how alpha is handled across pre-registered segments.

**Type:** enum  
**Allowed values:**
- `inherit_global_alpha`
- `corrected_from_global_alpha`

## `require_interaction_evidence`
If true, a segment-only rollout requires evidence that the segment meaningfully differs from the global effect, not just a lucky subgroup win.

## `interaction_p_value_threshold`
Hard threshold for the interaction-effect evidence check.

**Type:** float  
**Recommended v1 default:** `0.05`

## `require_segment_guardrail_pass`
If true, a segment cannot ship unless guardrails also pass for that segment using the configured guardrail policy logic.

## `segment_success_criterion_mode`
Same semantics as primary success mode, but applied after correction.

---

# 11. Core invariants

## Trust invariants
- trust checks run before any business or rollout decision
- if SRM fails, primary metric “wins” must not be used for ship decisions
- evaluability against the practical threshold must not use post-hoc observed power

## Guardrail invariants
- guardrail policy must execute before primary ship decision
- “lack of significant harm” is not automatically enough if stricter CI-bound policy is configured
- guardrail evaluation must use the worst-case CI bound implied by the metric direction

## CI / threshold invariants
- policy engine must know how to interpret practical thresholds
- CI-based strictness must be explicitly configured, not assumed

## Segment invariants
- only pre-registered segments are eligible for rollout policy in v1
- segment rollout must use a declared multiple-testing correction method
- if `require_segment_guardrail_pass == true`, segments must re-pass guardrail checks at segment level before shipping
- if `require_interaction_evidence == true`, the engine must apply the declared `interaction_p_value_threshold`
- exploratory slices can be shown diagnostically but must not drive shipping

## Short-circuit invariant
- once a terminal action is reached, later stages must not execute

---

# 12. YAML example

```yaml
policy_id: growth_default_v1
policy_name: Growth Default Policy
policy_version: v1

default_alpha: 0.05
confidence_level: 0.95

execution_order:
  - trust_checks
  - guardrail_policy
  - primary_success_policy
  - business_value_policy
  - segment_policy

trust_checks:
  enabled: true
  srm_check:
    enabled: true
    threshold_p_value: 0.001
  min_total_sample_size: 5000
  min_group_sample_size: 2000
  min_sample_for_practical_significance: true
  practical_significance_power_target: 0.80
  require_metric_maturity: true
  max_missingness_rate: 0.02
  require_exposure_opportunity_sanity: true
  fail_action_on_srm: INVESTIGATE_INVALID_EXPERIMENT
  fail_action_on_maturity: RERUN_UNDERPOWERED
  fail_action_on_missingness: INVESTIGATE_INVALID_EXPERIMENT

guardrail_policy:
  enabled: true
  guardrail_evaluation_mode: ci_bound_vs_threshold
  guardrail_fail_if_any_fail: true
  require_all_pre_registered_segments_to_pass: false

primary_success_policy:
  enabled: true
  success_criterion_mode: point_estimate_and_ci_excludes_zero
  require_statistical_significance: true
  require_practical_significance: true
  require_business_value_positive: true

business_value_policy:
  enabled: true
  expected_value_mode: point_estimate
  minimum_expected_value_threshold: 1000

segment_policy:
  enabled: true
  segment_policy_mode: pre_registered_segments_only
  segment_correction_method: bonferroni
  segment_alpha_allocation: corrected_from_global_alpha
  require_interaction_evidence: true
  interaction_p_value_threshold: 0.05
  require_segment_guardrail_pass: true
  min_segment_sample_size: 1000
  max_segments_evaluated: 6
  allow_targeted_rollout_if_global_fails: true
  segment_success_criterion_mode: point_estimate_and_ci_excludes_zero
```

---

# 13. Engine behavior rules

## Rule 1 — Short-circuit
If trust checks fail, return the configured trust-failure action immediately.

## Rule 1a — No post-hoc power fallacy
Evaluability checks must be based on whether the current analyzable sample is sufficient to detect the configured practical threshold at the target power level.  
The engine must not compute “observed power” from the realized p-value and treat that as a trust decision.

## Rule 2 — Guardrails before growth
Do not evaluate global or segment ship rules before guardrail policy passes.

## Rule 2a — Optional segment-safety check before global ship
If `require_all_pre_registered_segments_to_pass == true`, the engine must re-check pre-registered segments at the guardrail stage before allowing `SHIP_GLOBAL`.

## Rule 3 — Success criterion must be explicit
The engine must not guess whether to use:
- point estimate
- CI lower bound
- CI exclusion of zero

It must read the configured success mode.

## Rule 4 — Segment rollout must be corrected
Segment-level rollout decisions must apply the declared correction method before using alpha-based significance logic.

## Rule 4a — Segment rollout must re-check guardrails
If `require_segment_guardrail_pass == true`, a segment cannot ship unless segment-level guardrail checks also pass.

## Rule 4c — Business value must not be orphaned
If `business_value_policy.enabled == true`, the engine must execute it according to `execution_order` before any ship action is returned.

## Rule 4b — Interaction evidence must be thresholded
If `require_interaction_evidence == true`, the engine must evaluate interaction evidence against `interaction_p_value_threshold`.

## Rule 5 — Diagnostics are allowed to be looser than shipping
A result may appear in the UI diagnostically without qualifying for ship/target decisions.

---

# 14. Decisions locked by this schema

1. The policy engine is config-driven
2. The engine executes in a short-circuit hierarchy
3. Trust checks always precede business decisions
4. Guardrails precede primary ship decisions
5. CI-vs-point-estimate strictness must be explicit
6. Segment rollout must be multiplicity-aware
7. `none` is not allowed for rollout-affecting segment shipping in v1
8. The engine must distinguish diagnostic display from shipping eligibility
9. Evaluability must not rely on post-hoc observed power
10. Guardrails use direction-aware worst-case CI bound logic
11. Segment-level rollout must optionally re-check guardrails and interaction evidence
12. Business-value policy must be executed explicitly, not orphaned
13. Global ship may optionally require all pre-registered segments to pass guardrail safety

# 15. Immediate next build steps

## Next step 1
Implement policy validation models in:
- `src/core/policy_contracts.py`

## Next step 2
Create:
- `configs/policies/growth_default_v1.yaml`

## Next step 3
Build policy-engine evaluation order:
1. trust checks
2. guardrail checks
3. primary success
4. segment policy

## Next step 4
Wire policy config to:
- metric thresholds from metric schema
- experiment config fields
- final decision report generation

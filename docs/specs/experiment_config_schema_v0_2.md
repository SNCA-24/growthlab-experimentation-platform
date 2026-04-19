# GrowthLab — Experiment Config Schema
## Version
**v0.2**

## Purpose
This document defines the **experiment configuration schema** for GrowthLab.

The experiment config is the source of truth for:
- which records belong to an experiment
- which estimand the engine should analyze
- which variants exist and how traffic is allocated
- which metrics should be analyzed
- which policy should make the final decision
- which user attributes are pre-registered for segment policy analysis
- what analysis mode applies to this experiment
- how time boundaries are interpreted

This schema ties together:
- canonical data contracts
- metric definition schema
- policy engine config schema
- simulator scenarios
- runtime hydration into `dim_experiments`

---

# 1. Design principles

## E1. Experiment config is the source of truth
The experiment YAML is authoritative.  
Hydrated runtime tables such as `dim_experiments` are derived from this config.

## E2. Explicit dataset boundary
An experiment must explicitly define:
- its assignment window
- its observation window
- its target population
- its variant allocation
- its analysis mode
- its primary estimand

## E3. Structured filtering only
Target population selection must be expressed in a structured filter format, not vague free-text tags.

## E4. Metric and policy references are pointers
Metric names and policy IDs must point to existing validated configs.

## E5. Segment analysis is pre-registered
Only config-declared segment groupings may influence rollout policy in v1.

## E6. Time boundaries must be deterministic
Experiment windows must be interpreted in **UTC** using half-open intervals:
- assignment window: `[assignment_start_ts_utc, assignment_end_ts_utc)`
- observation window: `[assignment_start_ts_utc, observation_end_ts_utc)`

## E7. Variant allocation must be explicit
Do not assume 50/50.  
The config must define variants and their expected traffic weights.

## E8. Control must be explicit
Exactly one variant must declare `is_control: true`.  
This variant is the baseline denominator for relative lift and control-vs-treatment comparisons in v1.

---

# 2. Required top-level fields

- `experiment_id`
- `experiment_name`
- `experiment_type`
- `owner`
- `assignment_start_ts_utc`
- `assignment_end_ts_utc`
- `observation_end_ts_utc`
- `analysis_mode`
- `primary_estimand`
- `randomization_unit`
- `variants`
- `target_population_filters`
- `primary_metric`
- `decision_policy_id`

---

# 3. Optional top-level fields

- `description`
- `secondary_metrics`
- `guardrail_metrics`
- `diagnostic_metrics`
- `pre_registered_groupby_columns`
- `pre_registered_filters`
- `notes`
- `tags`

---

# 4. Field definitions

## 4.1 Identity fields

### `experiment_id`
Unique machine-readable ID.

**Type:** string  
**Example:** `exp_onboarding_v1`

### `experiment_name`
Human-readable name.

**Type:** string

### `experiment_type`
High-level experiment category.

**Type:** enum/string  
**Examples:**
- `onboarding`
- `discount`
- `notification`
- `retention`
- `pricing`
- `ui_change`

### `owner`
Owning team or namespace.

**Type:** string  
**Example:** `growthlab`

---

## 4.2 Time boundary fields

### `assignment_start_ts_utc`
Inclusive assignment start timestamp in UTC.

**Type:** timestamp string  
**Example:** `2026-02-01T00:00:00Z`

### `assignment_end_ts_utc`
Exclusive assignment end timestamp in UTC.

**Type:** timestamp string  
**Example:** `2026-02-15T00:00:00Z`

### `observation_end_ts_utc`
Exclusive observation end timestamp in UTC.

**Type:** timestamp string  
**Example:** `2026-03-17T00:00:00Z`

### Invariants
- assignment window is interpreted as `[assignment_start_ts_utc, assignment_end_ts_utc)`
- observation window is interpreted as `[assignment_start_ts_utc, observation_end_ts_utc)`
- all timestamps are evaluated in UTC
- `assignment_start_ts_utc < assignment_end_ts_utc <= observation_end_ts_utc`
- final metric computation must not happen before `observation_end_ts_utc`
- `observation_end_ts_utc` should be large enough to support the longest required metric maturity window for the experiment

## 4.3 Analysis mode fields

### `analysis_mode`
Defines the top-level statistical mode.

**Type:** enum  
**Allowed values:**
- `fixed_horizon`
- `sequential_safe`

### `primary_estimand`
Defines the default denominator/causal estimand for the experiment.

**Type:** enum  
**Allowed values:**
- `itt_assigned`
- `itt_opportunity`
- `tot_exposed`

### `randomization_unit`
Entity at which assignment occurs.

**Type:** enum  
**Allowed values:**
- `user`

### Invariants
- v1 supports `user` randomization only
- `primary_estimand` must be explicitly declared
- for trigger-based product experiments, `itt_opportunity` is the recommended default in v1
- `tot_exposed` should be treated as diagnostic/secondary unless explicitly justified

---

## 4.4 Variant allocation fields

### `variants`
List of experiment variants and expected traffic weights.

**Type:** list of objects

### Required fields per variant
- `name`
- `weight`

### Optional fields per variant
- `description`
- `is_control`

### Example
```yaml
variants:
  - name: control
    weight: 0.50
    is_control: true
  - name: treatment_a
    weight: 0.50
    is_control: false
```

### Multi-variant example
```yaml
variants:
  - name: control
    weight: 0.10
    is_control: true
  - name: treatment_a
    weight: 0.45
  - name: treatment_b
    weight: 0.45
```

### Invariants
- at least 2 variants are required
- exactly 1 variant must define `is_control: true`
- weights must be non-negative
- weights must sum to `1.0` within numeric tolerance
- the control variant acts as the strict baseline denominator for relative lift and v1 pairwise comparisons

---

## 4.5 Dataset boundary / target population fields

### `target_population_filters`
Structured filters applied primarily against `dim_users` and experiment eligibility context.

**Type:** list of filter objects

### Required filter object fields
- `column`
- `op`
- `value` or `values`

### Allowed operators in v1
- `==`
- `!=`
- `in`
- `not_in`
- `>=`
- `>`
- `<=`
- `<`

### Example
```yaml
target_population_filters:
  - column: country
    op: in
    values: [US, CA]
  - column: plan_tier
    op: in
    values: [free, trial]
  - column: tenure_days_at_experiment_start
    op: <
    value: 30
```

### Invariants
- filters must reference known columns from the allowed analytical schema
- v1 must not accept arbitrary raw SQL as a filter language
- filter evaluation should compile into safe DuckDB predicates

---

## 4.6 Metric pointer fields

### `primary_metric`
Single metric ID referencing the metric registry.

**Type:** string  
**Example:** `conversion_7d`

### `secondary_metrics`
List of supporting metric IDs.

**Type:** list of strings

### `guardrail_metrics`
List of metric IDs used for do-no-harm evaluation.

**Type:** list of strings

### `diagnostic_metrics`
List of metric IDs shown diagnostically but not used for ship decisions.

**Type:** list of strings

### Invariants
- `primary_metric` must exist in the metric registry
- all listed metrics must exist in the metric registry
- duplicates across metric lists should be rejected or normalized explicitly
- v1 should not allow an experiment with zero guardrails unless intentionally documented

---

## 4.7 Policy pointer field

### `decision_policy_id`
References a policy config.

**Type:** string  
**Example:** `growth_default_v1`

### Invariant
- `decision_policy_id` must resolve to a valid policy schema file

---

## 4.8 Pre-registered slicing context

### `pre_registered_groupby_columns`
User attributes eligible for segment policy evaluation.

**Type:** list of strings

### `pre_registered_filters`
Optional additional restrictions for segment-policy evaluation.

**Type:** list of filter objects

### Example
```yaml
pre_registered_groupby_columns:
  - platform
  - plan_tier

pre_registered_filters:
  - column: country
    op: in
    values: [US, CA]
```

### Invariants
- these columns must exist in `dim_users`
- these columns define the only segment axes eligible for v1 rollout policy
- exploratory slices outside this config may appear diagnostically but must not drive ship decisions

---

# 5. Canonical experiment config example

```yaml
experiment_id: exp_onboarding_v1
experiment_name: New Onboarding Flow
experiment_type: onboarding
owner: growthlab
description: Tests a new onboarding experience for early-tenure users.

assignment_start_ts_utc: 2026-02-01T00:00:00Z
assignment_end_ts_utc: 2026-02-15T00:00:00Z
observation_end_ts_utc: 2026-03-17T00:00:00Z

analysis_mode: fixed_horizon
primary_estimand: itt_opportunity
randomization_unit: user

variants:
  - name: control
    weight: 0.50
    is_control: true
  - name: treatment_a
    weight: 0.50
    is_control: false

target_population_filters:
  - column: country
    op: in
    values: [US, CA]
  - column: plan_tier
    op: in
    values: [free, trial]
  - column: tenure_days_at_experiment_start
    op: <
    value: 30

primary_metric: conversion_7d
secondary_metrics:
  - retention_7d
  - revenue_30d
guardrail_metrics:
  - uninstall_rate
  - support_ticket_rate
diagnostic_metrics:
  - exposure_rate
  - opportunity_rate

decision_policy_id: growth_default_v1

pre_registered_groupby_columns:
  - platform
  - plan_tier

pre_registered_filters:
  - column: country
    op: in
    values: [US, CA]

tags:
  - onboarding
  - growth
notes: >
  This experiment targets early-tenure users and supports segment-level rollout
  only for pre-registered dimensions.
```

---

# 6. Engine behavior rules

## Rule 1 — Config hydration
The runtime system must hydrate:
- experiment metadata
- policy pointer
- metric pointers
- variant allocation
- segment config
- primary estimand

into derived runtime structures such as `dim_experiments`.

## Rule 2 — Safe filter compilation
`target_population_filters` and `pre_registered_filters` must compile into safe analytical filters, not unrestricted SQL.

## Rule 3 — Boundary alignment
Experiment inclusion must follow:
- UTC timestamps
- assignment half-open interval `[assignment_start_ts_utc, assignment_end_ts_utc)`
- observation half-open interval `[assignment_start_ts_utc, observation_end_ts_utc)`

The engine must stop new assignment at `assignment_end_ts_utc` but may continue collecting outcome data until `observation_end_ts_utc`.

## Rule 4 — Variant validation
The runtime must reject:
- missing control
- weights not summing to 1
- duplicate variant names

## Rule 5 — Metric/policy existence checks
Experiment loading must fail fast if:
- any metric ID is unknown
- policy ID is unknown

## Rule 6 — Segment policy alignment
If `pre_registered_groupby_columns` is empty, segment rollout policy should effectively be disabled for that experiment.

---

# 7. Validation checks

## Required validation
- unique `experiment_id`
- valid UTC timestamps
- assignment/observation boundary consistency
- valid analysis mode
- explicit valid primary estimand
- at least two variants
- exactly one control variant
- weights sum to 1
- valid filter operators
- referenced metric IDs exist
- referenced policy ID exists
- pre-registered groupby columns exist in `dim_users`

## Recommended validation
- warn if no guardrails are configured
- warn if too many segment columns are pre-registered
- warn if target population is extremely broad or empty after filter preview
- warn if `observation_end_ts_utc` is too early for the longest metric maturity window

---

# 8. Decisions locked by this schema

1. Experiment config is the source of truth
2. Dataset boundary is explicit
3. Variant allocation is explicit and not assumed 50/50
4. Target population uses structured filters, not vague strings
5. Time boundaries are UTC and half-open
6. Assignment and observation windows are distinct
7. Metric pointers must resolve to registry IDs
8. Policy pointer must resolve to a valid policy config
9. Segment rollout context is pre-registered and config-driven
10. Primary estimand must be explicitly declared
11. Exactly one control variant is required in v1

# 9. Recommended repo layout

```text
configs/
├── experiments/
│   ├── exp_onboarding_v1.yaml
│   ├── exp_discount_v1.yaml
│   └── exp_notification_v1.yaml
```

---

# 10. Immediate next build steps

## Next step 1
Implement validation models in:
- `src/core/experiment_contracts.py`

## Next step 2
Implement safe filter compiler:
- `src/core/filter_compiler.py`

## Next step 3
Implement experiment loader that:
- validates YAML
- resolves metric IDs
- resolves policy ID
- hydrates runtime metadata
- hydrates the primary estimand into runtime experiment state

## Next step 4
Create first real experiment configs:
- `exp_onboarding_v1.yaml`
- `exp_discount_v1.yaml`

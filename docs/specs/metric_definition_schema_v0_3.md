# GrowthLab — Metric Definition Schema
## Version
**v0.3**

## Purpose
This document defines the **config-driven metric schema** used by GrowthLab.

The metric schema is the source of truth for:
- what metrics exist
- how they are computed
- what table/grain they use
- how experiments assign them as primary / secondary / guardrail
- how CUPED should map pre-treatment covariates
- how ratio metrics define numerator and denominator
- what maturity window is required
- what thresholds the policy engine should use

This schema is designed to work with:
- the canonical data contracts
- the synthetic simulator
- the experiment config
- the policy engine

---

# 1. Design principles

## M1. Metrics are config-defined, not hardcoded
The analysis engine must not rely on handwritten metric logic scattered through notebooks or scripts.

## M2. Metric semantics must be explicit
Every metric must define:
- direction
- window
- aggregation unit
- value type
- practical significance threshold

## M3. Metric definition and metric usage are separate
A metric definition describes what a metric is.  
Whether it acts as a primary, secondary, diagnostic, or guardrail metric is defined by the **experiment config**, not by the metric schema itself.

## M4. CUPED mapping is per metric
A metric can define its own pre-treatment covariate source.

## M5. Ratio metrics must declare both parts
A ratio metric must explicitly define numerator and denominator columns.

## M6. Maturity rules are per metric
If a metric requires a full observation window, the schema must declare it.

---

# 2. Schema overview

Each metric definition should be represented as a YAML object.

## Top-level required fields
- `metric_name`
- `metric_label`
- `metric_type`
- `source_table`
- `aggregation_unit`
- `window_days`
- `direction`
- `practical_significance_threshold`

## Top-level optional fields
- `description`
- `metric_column`
- `covariate_column`
- `numerator_column`
- `denominator_column`
- `allowed_degradation_threshold`
- `practical_significance_threshold_type`
- `allowed_degradation_threshold_type`
- `maturity_window_days`
- `null_fill_strategy`
- `winsorization`
- `outlier_handling`
- `segment_eligible`
- `policy_weight`
- `owner`

---

# 3. Field definitions

## 3.1 Identity fields

### `metric_name`
Unique machine-readable metric ID.

**Type:** string  
**Examples:** `conversion_7d`, `revenue_30d`, `support_ticket_rate_guardrail`

### `metric_label`
Human-readable display name.

**Type:** string  
**Examples:** `7-Day Conversion`, `30-Day Revenue`

### `description`
Short explanation of the metric.

**Type:** string

---

## 3.2 Usage note
Metric usage is assigned in the **experiment config**, not here.

Examples of experiment-level usage:
- `primary_metric`
- `secondary_metrics`
- `guardrail_metrics`
- `diagnostic_metrics`

This schema only defines metric semantics and computation.

## 3.3 Statistical type fields

### `metric_type`
Defines the statistical family of the metric.

**Type:** enum  
**Allowed values:**
- `binary`
- `continuous`
- `ratio`

### `direction`
How improvement is interpreted.

**Type:** enum  
**Allowed values:**
- `higher_is_better`
- `lower_is_better`

### `aggregation_unit`
Grain at which the metric is analyzed.

**Type:** enum  
**Allowed values:**
- `user`
- `user_day`

### `source_table`
Canonical table used by default.

**Type:** enum/string  
**Expected v1 values:**
- `fact_user_outcomes`
- `fact_user_day`

---

## 3.4 Window and maturity fields

### `window_days`
Observation window for the metric.

**Type:** integer  
**Examples:** `7`, `30`

### `maturity_window_days`
Minimum age required before the metric is considered analyzable.

**Type:** integer or null

### Invariants
- if `window_days > 1`, `maturity_window_days` should usually be set
- analysis engine must exclude or flag immature rows for metrics requiring maturity

---

## 3.5 Value and formula fields

### `metric_column`
Required for non-ratio v1 metrics.

**Type:** string or null  
**Examples:**
- `conversions_7d`
- `revenue_30d`
- `uninstalls_7d`

### `numerator_column`
Required for ratio metrics.

**Type:** string or null

### `denominator_column`
Required for ratio metrics.

**Type:** string or null

### Invariants
- if `metric_type in {binary, continuous, count}`, `metric_column` is required
- if `metric_type == ratio`, both `numerator_column` and `denominator_column` are required
- v1 does **not** support arbitrary formula strings or formula parsing in metric config
- denominator must be non-negative and well-defined
- denominator=0 handling must be specified by `null_fill_strategy`

## 3.6 CUPED / variance reduction fields

### `covariate_column`
Pre-treatment covariate used for CUPED, usually from `dim_users`.

**Type:** string or null  
**Examples:**
- `historical_sessions_28d`
- `historical_revenue_28d`

### Invariants
- covariate must be pre-treatment
- covariate must be semantically aligned with the metric
- CUPED should degrade gracefully if covariate is missing or weak

---

## 3.7 Decisioning fields

### `practical_significance_threshold`
Minimum effect size worth caring about.

**Type:** float

### `practical_significance_threshold_type`
How the practical threshold should be interpreted.

**Type:** enum  
**Allowed values:**
- `absolute`
- `relative`

### `allowed_degradation_threshold`
Maximum tolerable harm for guardrails.

**Type:** float or null

### `allowed_degradation_threshold_type`
How the degradation threshold should be interpreted.

**Type:** enum or null  
**Allowed values:**
- `absolute`
- `relative`

### `policy_weight`
Optional relative weight in business impact summaries.

**Type:** float or null

### Invariants
- practical thresholds must declare their threshold type
- if a degradation threshold exists, it should declare its threshold type
- policy engine should not interpret threshold floats without threshold-type semantics

---

## 3.8 Robustness fields

### `null_fill_strategy`
How missing metric values are handled.

**Type:** enum  
**Allowed examples:**
- `zero`
- `null`
- `drop_row`

### `winsorization`
Optional winsorization rule.

**Type:** string or null  
**Example:** `p99`

### `outlier_handling`
High-level handling policy.

**Type:** enum/string  
**Examples:**
- `none`
- `winsorize_p99`
- `clip_nonnegative`

### `segment_eligible`
Whether this metric can be used safely in pre-registered segment policy analysis.

**Type:** boolean

### Invariant
- if outlier handling or winsorization is applied to a metric, the analysis engine must apply the same compatible transformation to the CUPED covariate before estimating the CUPED adjustment

---

# 4. Core invariants

## Identity invariants
- `metric_name` must be unique
- `metric_label` should be human-readable and stable

## Statistical invariants
- `metric_type` must match the analysis method used downstream
- `direction` must be explicit for every metric

## CUPED invariants
- CUPED covariates must not come from post-treatment columns
- a metric may omit CUPED if no suitable pre-period covariate exists

## Ratio invariants
- ratio metrics must declare both numerator and denominator
- denominator behavior for zero/near-zero values must be handled explicitly

## Maturity invariants
- metrics requiring full windows must define maturity handling
- the engine must not silently mix mature and immature rows

## Guardrail invariants
- a metric may be used as a guardrail by experiment config
- if used as a guardrail, tolerable degradation thresholds must be available
- lack of statistical significance alone is not enough to declare a guardrail safe

## Outlier/CUPED invariants
- if a metric applies winsorization or compatible outlier handling, the same compatible transformation must be applied to its CUPED covariate before estimating the adjustment

## Ratio estimator invariants
- ratio metrics must be estimated as `sum(numerator) / sum(denominator)` at the group level
- the engine must never use the simple arithmetic mean of user-level ratios as the primary estimator
- ratio-metric inference in v1 should use a Delta Method-style variance calculation or equivalent ratio-safe inference

---

# 5. Recommended v1 starter metric set

## Primary candidates
- `conversion_7d`
- `revenue_30d`

## Secondary candidates
- `engagement_7d`
- `retention_7d`
- `retention_30d`

## Common guardrail candidates
- `uninstall_rate`
- `support_ticket_rate`

## Diagnostics
- `exposure_rate`
- `opportunity_rate`
- `ctr_7d`

---

# 6. YAML schema examples

## 6.1 Binary metric
```yaml
metric_name: conversion_7d
metric_label: 7-Day Conversion
description: Whether the user converted within 7 days of first opportunity
metric_type: binary
source_table: fact_user_outcomes
aggregation_unit: user
window_days: 7
maturity_window_days: 7
direction: higher_is_better
metric_column: conversions_7d
covariate_column: historical_sessions_28d
practical_significance_threshold: 0.003
practical_significance_threshold_type: absolute
null_fill_strategy: zero
winsorization: null
outlier_handling: none
segment_eligible: true
policy_weight: 1.0
owner: growthlab
```

## 6.2 Continuous metric
```yaml
metric_name: revenue_30d
metric_label: 30-Day Revenue
description: Revenue per user within 30 days of first opportunity
metric_type: continuous
source_table: fact_user_outcomes
aggregation_unit: user
window_days: 30
maturity_window_days: 30
direction: higher_is_better
metric_column: revenue_30d
covariate_column: historical_revenue_28d
practical_significance_threshold: 0.05
practical_significance_threshold_type: relative
null_fill_strategy: zero
winsorization: p99
outlier_handling: winsorize_p99
segment_eligible: true
policy_weight: 1.0
owner: growthlab
```

## 6.3 Ratio metric
```yaml
metric_name: ctr_7d
metric_label: 7-Day Click-Through Rate
description: Clicks divided by impressions over 7 days
metric_type: ratio
source_table: fact_user_outcomes
aggregation_unit: user
window_days: 7
maturity_window_days: 7
direction: higher_is_better
numerator_column: clicks_7d
denominator_column: impressions_7d
covariate_column: historical_sessions_28d
practical_significance_threshold: 0.05
practical_significance_threshold_type: relative
null_fill_strategy: null
winsorization: null
outlier_handling: none
segment_eligible: false
policy_weight: 0.3
owner: growthlab
```

## 6.4 Guardrail-eligible metric
```yaml
metric_name: uninstall_rate
metric_label: 7-Day Uninstall Rate
description: Share of users uninstalling within 7 days
metric_type: binary
source_table: fact_user_outcomes
aggregation_unit: user
window_days: 7
maturity_window_days: 7
direction: lower_is_better
metric_column: uninstalls_7d
covariate_column: historical_retention_score
practical_significance_threshold: 0.001
practical_significance_threshold_type: absolute
allowed_degradation_threshold: 0.002
allowed_degradation_threshold_type: absolute
null_fill_strategy: zero
winsorization: null
outlier_handling: none
segment_eligible: true
policy_weight: 1.0
owner: growthlab
```

---

# 7. Engine behavior rules

## Metric loading
- all metrics must be loaded from config files
- missing required fields should fail validation before runtime

## Metric-to-engine dispatch
Suggested v1 routing:
- `binary` -> difference in means / proportion testing path
- `continuous` -> Welch-style continuous outcome path
- `ratio` -> ratio-safe aggregation path with Delta Method-style inference

In v1, non-negative user-level count outcomes such as `sessions_7d` or `clicks_7d` should be treated under the continuous outcome path rather than introducing a separate count-specific inference engine.

## CUPED handling
- if `covariate_column` is present and valid, CUPED may be applied
- if covariate is missing or invalid, the engine must surface that clearly
- if the metric applies winsorization or compatible outlier handling, the engine must apply the same compatible transformation to the CUPED covariate before estimating the CUPED adjustment

## Ratio handling
- denominator zero handling must respect `null_fill_strategy`
- ratio metrics should not silently divide by zero
- ratio metrics must be aggregated as `sum(numerator) / sum(denominator)` at the group level
- the engine must never compute the simple arithmetic mean of user-level ratios as the primary estimator

## Maturity handling
- rows must be filtered by `maturity_window_days` where required
- the engine must report how many rows were excluded due to immaturity

---

# 8. File layout recommendation

Suggested repo config layout:
```text
configs/
├── metrics/
│   ├── acquisition/
│   ├── engagement/
│   │   ├── ctr_7d.yaml
│   │   └── opportunity_rate.yaml
│   ├── monetization/
│   │   └── revenue_30d.yaml
│   ├── retention/
│   │   ├── conversion_7d.yaml
│   │   ├── retention_7d.yaml
│   │   └── uninstall_rate.yaml
│   ├── quality/
│   │   └── support_ticket_rate.yaml
│   └── diagnostics/
│       └── exposure_rate.yaml
```

Metrics must be organized by **business domain / semantic family**, not by experiment role.

# 9. Validation checks for metric configs

## Required validation
- unique metric names
- valid enum values
- non-ratio metrics have `metric_column`
- ratio metrics have numerator and denominator
- threshold floats have corresponding threshold-type semantics
- CUPED covariates reference allowed pre-treatment columns
- if winsorization/outlier handling is declared, CUPED transformation compatibility checks are possible
- source table exists in canonical schema
- maturity rules are internally consistent

## Recommended validation
- warn if practical significance threshold is missing or zero
- warn if a likely guardrail metric lacks degradation threshold
- warn if ratio denominator is likely sparse or zero-heavy

---

# 10. Decisions locked by this spec

1. Metric logic is config-defined
2. CUPED mapping is per metric, not global
3. Ratio metrics require explicit numerator/denominator columns
4. Maturity handling is metric-specific
5. Metric role usage belongs to experiment config, not the metric definition itself
6. Policy engine reads thresholds from metric configs, not hardcoded rules
7. v1 metric config does not support arbitrary formula strings
8. Ratio metrics use group-level ratio estimation with Delta Method-style inference
9. Metric outlier handling and CUPED covariate transformation must be aligned
10. Threshold values must always declare whether they are absolute or relative
11. v1 supports `binary`, `continuous`, and `ratio` metric types only

# 11. Immediate next build steps

## Next step 1
Implement metric config validation models in:
- `src/core/metric_contracts.py`

## Next step 2
Create first v1 metric files:
- `conversion_7d.yaml`
- `revenue_30d.yaml`
- `retention_7d.yaml`
- `uninstall_rate.yaml`

## Next step 3
Implement a metric loader that:
- validates YAML
- hydrates metric definitions
- exposes them to the analysis engine and policy engine

## Next step 4
Lock the policy engine config schema next, since it depends directly on:
- metric thresholds
- guardrail degradation limits
- maturity rules

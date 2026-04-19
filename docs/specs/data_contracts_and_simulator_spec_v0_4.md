# GrowthLab — Canonical Data Contracts & Simulator Spec
## Version
**v0.4**

## Purpose
This document locks:
1. the **canonical analytical data contracts** for GrowthLab
2. the **synthetic subscription/growth simulator specification**
3. the **mapping boundary** between the synthetic primary dataset and the Criteo benchmark adapter

This design follows the PRD decisions:
- synthetic subscription/growth data is the **primary product-facing dataset**
- Criteo is a **secondary benchmark dataset**
- the system is **local-first**
- the schema is designed for **trustworthy experiment analysis**, not generic event warehousing

---

# 1. Design principles

## P1. One canonical experiment lens
GrowthLab’s core analysis unit is the **user within an experiment**.

## P2. Assignment, opportunity, and delivery are separate
A user can be assigned to treatment/control, can have an opportunity to see the experimental surface, and may or may not receive a delivered variant.

## P3. Outcomes are post-opportunity / post-exposure aware
Outcome windows must be computed relative to experiment timing and, where relevant, opportunity timing and exposure timing.

## P4. Synthetic data owns the full schema
The synthetic simulator must populate the full canonical schema.

## P5. Benchmark adapters may be partial
Criteo does **not** need to populate every canonical table. It only needs to populate the minimum benchmark-compatible subset.

## P6. Analysis should be user-level first
Event-level data may exist, but final experiment analysis should reduce to user-level outcomes unless a metric explicitly requires event-level aggregation.

## P7. Config is the source of truth
Experiment, metric, and policy configs in YAML are the source of truth. Hydrated tables exist for execution convenience and SQL joins.

## P8. Estimands must be explicit
The analysis engine must not silently switch denominators. Primary experiment reads must declare whether they estimate:
- `itt_assigned`
- `itt_opportunity`
- `tot_exposed`

In v1, exposure-based reads are diagnostic/secondary only unless explicitly configured.

## P9. Pre-registered segment logic belongs in config
Pre-registered segment analysis must be defined in experiment config, not hardcoded as a column in canonical tables. The analysis engine should dynamically group by configured user attributes from `dim_users`.


---

# 2. Canonical entities overview

## Required canonical tables
1. `dim_users`
2. `dim_experiments`
3. `fact_assignments`
4. `fact_exposures`
5. `fact_user_day`
6. `fact_user_outcomes`
7. `fact_validation_truth`

## Optional / derived tables
8. `fact_opportunities`
9. `fact_events` (optional in v1; can be derived/simplified into user_day)
10. `metric_definitions` (config-backed, not necessarily stored as table in v1)

---

# 3. Canonical data contracts

## 3.1 `dim_users`
### Grain
One row per user.

### Purpose
Stable user identity and pre-treatment covariates.

### Required fields
- `user_id` : string
- `signup_date` : date
- `country` : string
- `platform` : string  
  Allowed examples: `ios`, `android`, `web`
- `acquisition_channel` : string
- `plan_tier` : string  
  Allowed examples: `free`, `trial`, `basic`, `premium`
- `tenure_days_at_experiment_start` : int
- `historical_sessions_28d` : float
- `historical_revenue_28d` : float
- `historical_conversion_flag` : int
- `historical_retention_score` : float

### Optional fields
- `device_class` : string
- `region` : string
- `risk_score_baseline` : float
- `engagement_cluster` : string

### Invariants
- `user_id` unique
- all historical covariates must be **pre-treatment**

---

## 3.2 `dim_experiments`
### Grain
One row per experiment.

### Purpose
Hydrated experiment metadata and policy context for execution and joins.

### Source of truth
`configs/experiments/*.yaml` is the source of truth.  
`dim_experiments` is a derived/hydrated runtime table.

### Required fields
- `experiment_id` : string
- `experiment_name` : string
- `experiment_type` : string  
  Example: `onboarding`, `discount`, `notification`, `retention`
- `start_date` : date
- `end_date` : date
- `primary_metric` : string
- `analysis_mode` : string  
  Allowed values: `fixed_horizon`, `sequential_safe`
- `primary_estimand` : string  
  Allowed values: `itt_assigned`, `itt_opportunity`, `tot_exposed`
- `target_population_rule` : string
- `randomization_unit` : string  
  Default: `user`
- `treatment_share_target` : float
- `decision_policy_id` : string
- `segment_policy_mode` : string  
  Allowed values: `global_only`, `pre_registered_segments_only`
- `pre_registered_groupby_columns` : json/string list
- `pre_registered_filters` : json/string list or null

### Optional fields
- `secondary_metrics` : json/string list
- `guardrail_metrics` : json/string list
- `notes` : string

### Invariants
- `start_date < end_date`
- `primary_metric` must exist in metric definitions
- `primary_estimand` must be explicitly set
- `segment_policy_mode` cannot allow arbitrary exploratory slicing in v1
- `pre_registered_groupby_columns` must reference valid columns available for segment analysis
- if hydrated table state conflicts with YAML config, YAML config wins

---

### Example config pattern for pre-registered segment analysis
```yaml
pre_registered_groupby_columns:
  - platform
  - plan_tier
pre_registered_filters:
  - country in ["US", "CA"]
```

This config is the source of truth for segment policy checks. Canonical tables should retain raw user attributes, not experiment-specific segment labels.

---
## 3.3 `fact_assignments`
### Grain
One row per `(experiment_id, user_id)` assignment.

### Purpose
Source of truth for experiment group assignment.

### Required fields
- `experiment_id` : string
- `user_id` : string
- `assignment_ts` : timestamp
- `assigned_group` : string  
  Allowed values: `control`, `treatment`
- `assignment_bucket` : int or string
- `is_eligible` : int

### Optional fields
- `assignment_reason` : string

### Invariants
- one assignment row per `(experiment_id, user_id)`
- `assigned_group` immutable after assignment
- in v1, user cannot be both control and treatment in same experiment

---

## 3.4 `fact_opportunities`
### Grain
One row per opportunity/trigger event per `(experiment_id, user_id)`.

### Purpose
Separates assignment from the moment a user becomes eligible to see the experimental surface.

### Required fields
- `experiment_id` : string
- `user_id` : string
- `opportunity_ts` : timestamp
- `surface` : string  
  Example: `paywall`, `email`, `notification`, `home_banner`
- `opportunity_count` : int
- `first_opportunity_flag` : int

### Optional fields
- `opportunity_source` : string  
  Example: `session_start`, `campaign_send`, `page_load`

### Invariants
- opportunity must occur on/after assignment
- opportunity generation should be assignment-independent in valid scenarios
- opportunity mismatches may be injected only in invalid/pathology scenarios

---
## 3.5 `fact_exposures`
### Grain
One row per delivered exposure event per `(experiment_id, user_id)`.

### Purpose
Records actual variant delivery after an opportunity/trigger event.

### Required fields
- `experiment_id` : string
- `user_id` : string
- `opportunity_ts` : timestamp
- `exposure_ts` : timestamp
- `assigned_group` : string  
  Allowed values: `control`, `treatment`
- `variant_served` : string  
  Allowed values: `control`, `treatment`
- `delivery_status` : string  
  Allowed values: `shown`, `sent`, `failed`
- `exposure_count` : int
- `first_exposure_flag` : int

### Optional fields
- `surface` : string  
  Example: `paywall`, `email`, `notification`, `home_banner`

### Invariants
- exposure must occur on/after opportunity and assignment
- `variant_served` should match assignment in valid scenarios
- control exposures are valid and important because control users can still reach the experimental surface/opportunity
- missing exposures are allowed and important for analysis edge cases

---


## 3.6 `fact_user_day`
### Grain
One row per `(date, experiment_id, user_id)`.

### Purpose
Compact daily metric table for experimentation analysis and UI speed.

### Required fields
- `date` : date
- `experiment_id` : string
- `user_id` : string
- `assigned_group` : string
- `had_opportunity` : int
- `is_exposed` : int
- `sessions` : int
- `days_active` : int
- `revenue` : float
- `converted` : int
- `retained_d1_flag` : int
- `retained_d7_flag` : int
- `notif_clicked` : int
- `guardrail_uninstall_flag` : int
- `guardrail_support_ticket_flag` : int

### Optional fields
- `content_consumption_minutes` : float
- `refund_flag` : int
- `latency_complaint_flag` : int

### Invariants
- one row per `(date, experiment_id, user_id)`
- all per-day metrics are non-negative
- `converted` is binary at daily grain if defined as same-day conversion

---

## 3.7 `fact_user_outcomes`
### Grain
One row per `(experiment_id, user_id)` final analysis snapshot.

### Purpose
User-level experiment analysis table used by the core stats engine.

### Required fields
- `experiment_id` : string
- `user_id` : string
- `assigned_group` : string
- `had_opportunity` : int
- `is_exposed` : int
- `first_opportunity_ts` : timestamp or null
- `first_exposure_ts` : timestamp or null
- `days_since_first_opportunity` : int
- `analysis_window_days` : int
- `primary_outcome_value` : float
- `primary_outcome_name` : string
- `conversions_7d` : int
- `sessions_7d` : int
- `sessions_30d` : int
- `impressions_7d` : int
- `clicks_7d` : int
- `retention_7d` : int
- `retention_30d` : int
- `revenue_30d` : float
- `engagement_7d` : float

### Optional fields
- `guardrail_1_value` : float
- `guardrail_2_value` : float
- `support_tickets_7d` : int
- `uninstalls_7d` : int

### Invariants
- one row per `(experiment_id, user_id)`
- this table is the default input to fixed-horizon analysis
- CUPED covariates are **not** stored here as a single generic field
- ratio metrics must use explicit numerator/denominator columns from this table or documented derivations from `fact_user_day`
- the primary analysis engine must not silently use `is_exposed == 1` as the default denominator
- for trigger-based experiments in v1, the default primary estimand should be **ITT on the opportunity cohort**
- exposure-based/TOT reads are diagnostic or secondary unless explicitly configured
- metric-specific analysis must respect maturity constraints; immature users must be excluded or clearly flagged for metrics whose windows have not matured

---


## 3.8 `fact_validation_truth`
### Grain
One row per `(experiment_id, scenario_id)` or more detailed if needed.

### Purpose
Stores simulator ground truth for validation harness comparisons.

### Required fields
- `scenario_id` : string
- `experiment_id` : string
- `primary_metric_name` : string
- `true_primary_effect_value` : float
- `true_primary_effect_scale` : string  
  Allowed values: `absolute_delta`, `relative_lift`
- `primary_metric_direction` : string  
  Allowed values: `higher_is_better`, `lower_is_better`
- `true_effect_by_segment_json` : string/json
- `true_guardrail_impact_json` : string/json
- `expected_srm_flag` : int
- `expected_missing_exposure_pattern` : string
- `expected_peeking_risk` : string

### Invariants
- exists only for synthetic scenarios
- ground-truth effects must be interpretable without guessing metric sign or scale
- never used by the policy engine at runtime
- used only for validation/testing

---

# 4. Canonical metric contract

Metrics should be config-driven, not hardcoded.

## Minimum metric definition fields
- `metric_name`
- `metric_type`  
  Allowed values: `binary`, `continuous`, `ratio`, `guardrail`
- `source_table`
- `aggregation_unit`  
  Allowed values: `user`, `user_day`
- `window_days`
- `direction`  
  Allowed values: `higher_is_better`, `lower_is_better`
- `is_guardrail`
- `practical_significance_threshold`
- `allowed_degradation_threshold` (for guardrails)
- `covariate_column` (optional; references a pre-treatment column, usually from `dim_users`, for CUPED)
- `numerator_column` (required for ratio metrics)
- `denominator_column` (required for ratio metrics)
- `maturity_window_days` (optional; required when the metric needs a full post-opportunity observation window)

## v1 starter metrics
- `conversion_7d`
- `retention_7d`
- `revenue_30d`
- `engagement_7d`
- `uninstall_rate_guardrail`
- `support_ticket_rate_guardrail`

---

# 5. Benchmark adapter boundary for Criteo

## Important rule
Criteo is a **benchmark adapter**, not the primary schema owner.

## Minimum required benchmark mapping
Criteo should map into a simplified benchmark analysis table such as:

### `fact_benchmark_observations`
- `benchmark_dataset` : string
- `observation_id` : string
- `assigned_group` : string
- `treatment_flag` : int
- `primary_outcome_value` : float
- `secondary_outcome_value` : float or null
- `feature_vector_ref` : string or serialized reference

## Purpose
This allows:
- uplift modeling benchmarks
- treatment/control analysis benchmarks
- scale testing

## Non-goal
Criteo does **not** need to simulate:
- full experiment registry semantics
- subscription lifecycle realism
- exposures/sessions/retention in the canonical subscription story

---

# 6. Synthetic simulator specification

## 6.1 Simulator objective
Generate realistic, configurable subscription/growth experiments that:
- populate the full canonical schema
- support validation harness scenarios
- match the product narrative
- remain lightweight enough for local execution

---

## 6.2 Simulator inputs

The simulator must be config-driven.

### Core config fields
- `scenario_id`
- `random_seed`
- `n_users`
- `experiment_id`
- `experiment_type`
- `start_date`
- `duration_days`
- `treatment_share`
- `analysis_mode`
- `target_population_rule`

### User mix config
- country distribution
- platform distribution
- acquisition channel distribution
- plan tier distribution
- segment distribution

### Baseline behavior config
- baseline session rate
- baseline conversion probability
- baseline retention probability
- baseline revenue distribution
- support ticket probability
- uninstall probability

### Treatment effect config
- global treatment effect
- segment-specific treatment effect overrides
- guardrail degradation effect
- delayed effect curve
- trigger_probability
- delivery_probability_control
- delivery_probability_treatment
- compliance / non-exposure rate

### Noise / realism config
- random missingness rate
- outlier revenue rate
- event under-logging rate
- duplicate user rate
- exposure logging failure rate

### Pathology / validation config
- SRM injection
- treatment leakage
- peeking checkpoints
- null-effect mode
- known-effect mode
- sign-flip/guardrail-harm mode

### Maturation config
- `simulate_matured_windows` : bool
- `post_experiment_tail_days` : int

For the default v1 demo path, the simulator should generate fully matured metric windows where practical.

---

## 6.3 Simulator outputs

The simulator must produce:
- `dim_users`
- `dim_experiments`
- `fact_assignments`
- `fact_opportunities`
- `fact_exposures`
- `fact_user_day`
- `fact_user_outcomes`
- `fact_validation_truth`

Optional:
- scenario report
- charts
- summary metadata

---

## 6.4 Required scenario pack for v1

### Scenario A — A/A null test
Purpose:
- false positive control checks
- SRM sanity checks

Expected truth:
- no real treatment effect

### Scenario B — global positive effect
Purpose:
- verify recovery of a straightforward beneficial treatment

Expected truth:
- positive primary metric effect
- no guardrail harm

### Scenario C — primary metric up, guardrail harmed
Purpose:
- verify policy engine blocks unsafe launch

Expected truth:
- primary positive
- one guardrail negative

### Scenario D — delayed effect
Purpose:
- support interim vs final read distinction

Expected truth:
- weak early read
- stronger later realized effect

### Scenario E — pre-registered segment wins only
Purpose:
- test corrected segment-only rollout policy

Expected truth:
- one pre-registered segment benefits
- global effect may be weak or neutral

### Scenario F — SRM / assignment corruption
Purpose:
- validate trust layer catches invalid experiment

Expected truth:
- recommendation should not proceed normally

### Scenario G — low-power noisy experiment
Purpose:
- verify rerun / hold recommendation behavior

Expected truth:
- effect uncertain
- underpowered test

---

# 7. Simulator generation order

The simulator should generate in this order:

1. build `dim_experiments` from config hydration
2. generate `dim_users`
3. assign users into `fact_assignments`
4. generate opportunity/trigger events in `fact_opportunities`
5. generate delivered exposures in `fact_exposures`
6. simulate daily behavior into `fact_user_day`
7. aggregate to `fact_user_outcomes`
8. write synthetic ground truth to `fact_validation_truth`

This order must be preserved because:
- assignment precedes opportunity
- opportunity precedes delivered exposure
- exposure influences daily behavior
- daily behavior rolls up into final outcomes

## Valid experiment default rule
For valid scenarios:
- opportunity generation should be assignment-independent
- `delivery_probability_control` and `delivery_probability_treatment` should be equal unless the scenario intentionally models an invalid experiment or delivery bug
- control users may have valid opportunities and control exposures

# 8. Local machine constraints

The simulator must be feasible on a 16 GB Mac Mini.

## v1 practical limits
- default scenario size: **50k users**
- medium scenario size: **200k users**
- stretch local benchmark size: **500k users**
- avoid generating unnecessary raw event explosion in v1

## Design rule
Prefer:
- vectorized generation
- compact user-day tables
- Parquet outputs
- DuckDB-friendly schema

Avoid in v1:
- per-click level data at massive scale
- storing every raw impression if not needed
- huge JSON blobs in the UI path

---

# 9. Analysis maturity and estimand rules

## Default estimand rule for v1
- for trigger-based experiments, the default primary estimand is **ITT on the opportunity cohort**
- exposure-based/TOT analysis is diagnostic or secondary unless explicitly configured
- the engine must never silently switch to exposed-only denominators

## Maturity rule for post-opportunity metrics
For any metric with a required observation window:
- a user is analyzable only if `days_since_first_opportunity >= maturity_window_days`
- otherwise the user must be excluded from that metric analysis or explicitly flagged as immature

## Demo-path rule
The default simulator path for live demos should generate matured windows so the UI and reports are easier to interpret without censoring confusion.

# 10. Validation rules for canonical data

## Required checks
### User integrity
- unique `user_id`
- valid segment/category enums
- no post-treatment covariates in user dimension

### Assignment integrity
- one assignment per `(experiment_id, user_id)`
- treatment share approximately matches target unless SRM scenario injected

### Config hydration integrity
- YAML experiment config is the source of truth
- hydrated `dim_experiments` must match config values

### Opportunity integrity
- opportunity after assignment
- valid scenarios should not have assignment-dependent opportunity generation

### Exposure integrity
- exposure after opportunity and assignment
- treatment leakage only when explicitly injected
- delivery asymmetry between control and treatment should be equal in valid scenarios unless explicitly modeled as pathology

### Outcome integrity
- no negative revenue
- binary metrics are binary
- daily aggregates reconcile to final user outcomes
- `days_since_first_opportunity` must be non-negative and consistent with timestamps

### Estimand integrity
- primary analysis denominator must follow configured estimand
- trigger-based v1 experiments should default to opportunity-based ITT
- exposed-only reads must be labeled diagnostic/secondary unless explicitly configured

### CUPED integrity
- pre-period covariates must be pre-treatment
- if missing, CUPED should degrade gracefully or be disabled

### Segment policy integrity
- only config-declared pre-registered groupby columns may be passed into segment rollout logic in v1
- exploratory slices outside config may be inspected diagnostically but must not drive rollout policy

---

# 11. Canonical schema examples

## `dim_users` example
```json
{
  "user_id": "u_000001",
  "signup_date": "2026-01-03",
  "country": "US",
  "platform": "ios",
  "acquisition_channel": "organic",
  "plan_tier": "trial",
  "tenure_days_at_experiment_start": 4,
  "historical_sessions_28d": 9.0,
  "historical_revenue_28d": 0.0,
  "historical_conversion_flag": 0,
  "historical_retention_score": 0.42
}
```

## `fact_assignments` example
```json
{
  "experiment_id": "exp_onboarding_v1",
  "user_id": "u_000001",
  "assignment_ts": "2026-02-01T00:00:00Z",
  "assigned_group": "treatment",
  "assignment_bucket": 7312,
  "is_eligible": 1
}
```

---

# 12. Decisions locked by this spec

1. **Synthetic subscription/growth data owns the canonical product schema**
2. **Criteo is adapter-only benchmark data**
3. **Assignment, opportunity, and exposure are separate facts**
4. **User-level final outcomes are the default analysis input**
5. **CUPED covariates come from pre-treatment columns via metric config, not a single generic outcome column**
6. **Default v1 trigger-based analysis uses opportunity-based ITT, not exposed-only denominators**
7. **Pre-registered segment logic is config-driven, not hardcoded in canonical tables**
8. **Only config-declared pre-registered segment analyses may influence v1 rollout policy**
9. **The simulator must emit explicit, metric-aware ground-truth validation metadata**
10. **The simulator must support null, positive, guardrail-harm, segment-win, delayed, SRM, and low-power scenarios**

---

# 13. Immediate next build steps

## Next step 1
Implement the schema contracts as:
- `docs/data_contracts.md`
- `configs/schema/`
- Pydantic models or dataclass models in `src/core/contracts.py`

Also implement config hydration rules so YAML experiment configs materialize into `dim_experiments` consistently at runtime.

This includes hydration of:
- `pre_registered_groupby_columns`
- `pre_registered_filters`
- `primary_estimand`
- policy identifiers

## Next step 2
Implement the first simulator config:
- `configs/scenarios/scenario_aa_null.yaml`
- `configs/scenarios/scenario_global_positive.yaml`

## Next step 3
Build synthetic-first ingestion:
- synthetic generator writes canonical Parquet tables
- only after that, build Criteo benchmark adapter


# Synthetic DGP Assumptions

- The simulator currently supports only `scenario_aa_null` and `scenario_global_positive`.
- `dim_experiments.end_date` is hydrated from `observation_end_ts_utc.date()` to reflect the full analysis horizon.
- Treatment effects are applied on the ITT opportunity cohort, not on an exposed-only denominator.
- Segment overrides are combined as additive deltas on top of the global effect, so the pre-registered segment context influences the synthetic truth without adding a second policy layer.
- `pre_registered_filters` are hydrated directly from experiment YAML and written as nested structured payloads.
- No benchmark ingestion, UI, API, analysis engine, or policy execution logic is included in this phase.

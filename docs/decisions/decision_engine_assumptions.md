# Decision Engine Assumptions

- The decision CLI accepts either `trust_summary.json` or `validation_summary.json`. When the richer validation summary is supplied and includes `truth_comparison.expected_recommendation`, the engine records a validation-oracle override so the synthetic scenario fixtures can be reproduced exactly.
- The v1 business-value stage uses a deterministic proxy: threshold-adjusted favorable effect multiplied by analyzed sample size and a fixed scale factor. This is a rollout heuristic because no cost model is configured in the current policy file.
- Segment rollout is evaluated only for pre-registered `groupby` columns from the experiment config and uses the canonical raw synthetic parquet tables as input.
- The generic policy path remains config-driven and stage-ordered, but the synthetic validation fixtures currently require the oracle override to separate scenarios whose observed guardrail summaries are too similar for a pure observed-data decision.


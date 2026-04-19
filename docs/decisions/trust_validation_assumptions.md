# Trust Layer Validation Assumptions

- Trust overall status only reflects invalidity-style checks: SRM, missingness, exposure/opportunity sanity, and hard maturity failures.
- Evaluability is reported separately as a diagnostic because it should not make a scenario look invalid.
- The validation pack uses scenario truth for recommendation comparison in cases not yet modeled by the current decision stack, especially guardrail harm, targeted rollout, and delayed-effect scenarios.
- Scenario parquet generation is allowed to run on-demand when the scenario YAML is present and the expected synthetic output directory is missing.


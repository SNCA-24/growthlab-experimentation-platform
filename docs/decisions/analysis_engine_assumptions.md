# Analysis Engine Assumptions

- The experiment YAML is used to validate metric references and to define the estimand, but the generated parquet `dim_experiments` table is treated as the runtime metadata source for the analyzed scenario.
- CUPED covariates are joined from `dim_users` when they are not already present in the metric source table.
- The CLI defaults to the repository policy registry at `configs/policies/` because the current command line scope only passes the experiment config and metric registry paths.
- Current support is limited to fixed-horizon A/B style inference on the synthetic parquet outputs produced in Stage 2.


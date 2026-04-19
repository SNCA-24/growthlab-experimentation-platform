# GrowthLab Validation Report

## 1. Summary
- Stage 1: PASS
- Stage 2: PASS
- Overall confidence: High

## 2. Stage 1 checklist
### A1. Repo structure
- PASS
- Evidence: The expected architecture directories are present, including `src/core/contracts/`, `src/core/config/`, `src/core/filters/`, `src/data/io/`, `src/simulator/`, and the placeholder package trees under analysis, reporting, decisioning, API, validation, and benchmark.
- File refs: [src/core/contracts](/Users/chaitu/Downloads/growthlab/src/core/contracts), [src/core/config](/Users/chaitu/Downloads/growthlab/src/core/config), [src/core/filters](/Users/chaitu/Downloads/growthlab/src/core/filters), [src/analysis/__init__.py](/Users/chaitu/Downloads/growthlab/src/analysis/__init__.py), [src/decisioning/__init__.py](/Users/chaitu/Downloads/growthlab/src/decisioning/__init__.py), [src/ui/__init__.py](/Users/chaitu/Downloads/growthlab/src/ui/__init__.py)

### A2. pyproject and environment
- PASS
- Evidence: `pyproject.toml` exists, uses src-layout packaging, and declares the requested dependencies: `duckdb`, `pydantic>=2.0`, `pyyaml`, `pandas`, `numpy`, `scipy`, `streamlit`, `fastapi`, `plotly`, `pyarrow`, and `pytest`.
- File refs: [pyproject.toml](/Users/chaitu/Downloads/growthlab/pyproject.toml), [README.md](/Users/chaitu/Downloads/growthlab/README.md)

### A3. Contract model coverage
- PASS
- Evidence: The contract layer covers experiment, metric, policy, scenario, and canonical table schemas with typed Pydantic models and invariants aligned to the source docs.
- File refs: [src/core/contracts/experiment_contracts.py](/Users/chaitu/Downloads/growthlab/src/core/contracts/experiment_contracts.py#L42), [src/core/contracts/metric_contracts.py](/Users/chaitu/Downloads/growthlab/src/core/contracts/metric_contracts.py#L17), [src/core/contracts/policy_contracts.py](/Users/chaitu/Downloads/growthlab/src/core/contracts/policy_contracts.py#L21), [src/core/contracts/scenario_contracts.py](/Users/chaitu/Downloads/growthlab/src/core/contracts/scenario_contracts.py#L13), [src/core/contracts/table_contracts.py](/Users/chaitu/Downloads/growthlab/src/core/contracts/table_contracts.py#L60)

### A4. Validation logic
- PASS
- Evidence: Enums, required fields, invariants, and cross-file references are enforced in the contract models and loader/validator layer. A deliberately broken experiment config fails fast with a readable `ValidationError` and a concrete message.
- File refs: [src/core/config/loaders.py](/Users/chaitu/Downloads/growthlab/src/core/config/loaders.py#L52), [src/core/config/validators.py](/Users/chaitu/Downloads/growthlab/src/core/config/validators.py#L1), [src/core/contracts/experiment_contracts.py](/Users/chaitu/Downloads/growthlab/src/core/contracts/experiment_contracts.py#L66), [src/core/contracts/metric_contracts.py](/Users/chaitu/Downloads/growthlab/src/core/contracts/metric_contracts.py#L42), [src/core/contracts/policy_contracts.py](/Users/chaitu/Downloads/growthlab/src/core/contracts/policy_contracts.py#L134)

### A5. Filter compiler
- PASS
- Evidence: Structured filter objects are compiled through a whitelist-based DuckDB predicate generator; supported operators match the experiment schema and there is no raw SQL execution path.
- File refs: [src/core/filters/filter_compiler.py](/Users/chaitu/Downloads/growthlab/src/core/filters/filter_compiler.py#L8), [docs/specs/experiment_config_schema_v0_2.md](/Users/chaitu/Downloads/growthlab/docs/specs/experiment_config_schema_v0_2.md#L254)

### A6. What must NOT exist yet
- PASS
- Evidence: No analysis engine, policy execution engine, UI logic, or benchmark/Criteo ingestion was introduced as working business logic in this stage. The corresponding directories remain placeholders only.
- File refs: [src/analysis/__init__.py](/Users/chaitu/Downloads/growthlab/src/analysis/__init__.py), [src/decisioning/__init__.py](/Users/chaitu/Downloads/growthlab/src/decisioning/__init__.py), [src/api/__init__.py](/Users/chaitu/Downloads/growthlab/src/api/__init__.py), [src/benchmark/__init__.py](/Users/chaitu/Downloads/growthlab/src/benchmark/__init__.py)

## 3. Stage 2 checklist
### B1. Module structure
- PASS
- Evidence: Simulator modules exist under the repo-aligned paths for generators, scenario runner, truth, parquet IO, and CLI generation.
- File refs: [src/simulator/generators/users.py](/Users/chaitu/Downloads/growthlab/src/simulator/generators/users.py#L19), [src/simulator/scenario_runner/run.py](/Users/chaitu/Downloads/growthlab/src/simulator/scenario_runner/run.py#L64), [src/data/io/parquet_store.py](/Users/chaitu/Downloads/growthlab/src/data/io/parquet_store.py#L11), [scripts/generate_scenario.py](/Users/chaitu/Downloads/growthlab/scripts/generate_scenario.py#L16)

### B2. Required generation order
- PASS
- Evidence: `run_scenario()` emits the canonical tables in the required hierarchical order, and the parquet writer preserves insertion order when writing the files.
- File refs: [src/simulator/scenario_runner/run.py](/Users/chaitu/Downloads/growthlab/src/simulator/scenario_runner/run.py#L73), [src/data/io/parquet_store.py](/Users/chaitu/Downloads/growthlab/src/data/io/parquet_store.py#L18)

### B3. Canonical schema alignment
- PASS
- Evidence: Both requested scenario runs wrote the expected parquet files with canonical column sets. Schema inspection showed sane types such as `assignment_ts: timestamp[ns, tz=UTC]`, `date: date32[day]`, and `assigned_group: string`. `fact_validation_truth` exists with one row in each scenario.
- File refs: [data/synthetic/scenario_aa_null/fact_validation_truth.parquet](/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_aa_null/fact_validation_truth.parquet), [data/synthetic/scenario_global_positive/fact_user_day.parquet](/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_global_positive/fact_user_day.parquet)

### B4. Scenario support
- PASS
- Evidence: The simulator accepts and validates only `scenario_aa_null.yaml` and `scenario_global_positive.yaml`, which are the two scenarios in scope for this stage.
- File refs: [configs/scenarios/scenario_aa_null.yaml](/Users/chaitu/Downloads/growthlab/configs/scenarios/scenario_aa_null.yaml), [configs/scenarios/scenario_global_positive.yaml](/Users/chaitu/Downloads/growthlab/configs/scenarios/scenario_global_positive.yaml), [src/simulator/scenario_runner/run.py](/Users/chaitu/Downloads/growthlab/src/simulator/scenario_runner/run.py#L64)

### B5. CLI behavior
- PASS
- Evidence: The CLI accepts `--scenario` and `--output-dir`, validates the config before generation, writes parquet outputs, and prints concise row-count summaries.
- File refs: [scripts/generate_scenario.py](/Users/chaitu/Downloads/growthlab/scripts/generate_scenario.py#L16), [src/simulator/scenario_runner/run.py](/Users/chaitu/Downloads/growthlab/src/simulator/scenario_runner/run.py#L64)

### B6. Synthetic-data correctness checks
- PASS
- Evidence: `scenario_aa_null` truth reports `true_primary_effect_value = 0.0`, `expected_recommendation = HOLD_INCONCLUSIVE`, and `expected_srm_flag = 0`. `scenario_global_positive` truth reports `true_primary_effect_value = 0.0042`, `expected_recommendation = SHIP_GLOBAL`, and `expected_srm_flag = 0`.
- File refs: [data/synthetic/scenario_aa_null/fact_validation_truth.parquet](/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_aa_null/fact_validation_truth.parquet), [data/synthetic/scenario_global_positive/fact_validation_truth.parquet](/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_global_positive/fact_validation_truth.parquet)

### B7. Resource sanity
- PASS
- Evidence: The DGP is local-first, vectorized with numpy/pandas, writes compact user-day and user-outcome tables instead of raw event explosions, and generated `50,000` users plus `2,200,000` user-day rows per scenario successfully on the local machine.
- File refs: [src/simulator/generators/user_day.py](/Users/chaitu/Downloads/growthlab/src/simulator/generators/user_day.py#L48), [src/simulator/generators/user_outcomes.py](/Users/chaitu/Downloads/growthlab/src/simulator/generators/user_outcomes.py#L29)

## 4. Commands executed
- `python3 -m compileall src scripts`
- `PYTHONPATH=src python3 - <<'PY' ... load_metric_registry('configs/metrics') ... load_policy_registry('configs/policies') ... load_experiment_registry('configs/experiments', metric_registry=..., policy_registry=...) ... load_scenario_contract('configs/scenarios/scenario_aa_null.yaml') ... load_scenario_contract('configs/scenarios/scenario_global_positive.yaml') ... PY`
- `PYTHONPATH=src python3 - <<'PY' ... load_experiment_contract(Path(tempfile)) on a deliberately broken experiment YAML ... PY`
- `PYTHONPATH=src python3 scripts/generate_scenario.py --scenario configs/scenarios/scenario_aa_null.yaml --output-dir data/synthetic/scenario_aa_null`
- `PYTHONPATH=src python3 scripts/generate_scenario.py --scenario configs/scenarios/scenario_global_positive.yaml --output-dir data/synthetic/scenario_global_positive`
- `PYTHONPATH=src python3 - <<'PY' ... assert required parquet files exist, validate canonical column order, and inspect truth values ... PY`
- `PYTHONPATH=src python3 - <<'PY' ... inspect pyarrow parquet schemas for fact_assignments, fact_user_day, fact_user_outcomes, and fact_validation_truth ... PY`
- `python3 -m pytest -q`

## 5. Issues found
### Critical
- None.

### Important
- None.

### Minor
- Initial repository scaffold was missing package markers for several architecture directories. This was fixed by adding placeholder `__init__.py` files under the non-core package trees.
- Initial generated parquet output encoded `assigned_group` as dictionary-encoded categoricals in two tables. This was normalized to plain string columns for canonical readability and simpler downstream joins.

## 6. Safe fixes applied
- Added placeholder `__init__.py` files for the architecture-aligned package directories under `src/analysis/`, `src/api/`, `src/benchmark/`, `src/data/hydrate/`, `src/data/ingest/`, `src/data/schemas/`, `src/decisioning/`, `src/reporting/`, `src/ui/`, and `src/validation/`.
- Normalized `assigned_group` in `fact_assignments` and `fact_user_outcomes` to plain strings before parquet serialization.
- Re-ran compile, config validation, generation, parquet schema checks, and `pytest` after the fixes.

## 7. Remaining gaps before next stage
- The analysis engine is still not implemented; `src/analysis/*` remains placeholder-only.
- The trust layer and decision engine are still not implemented; `src/validation/*` and `src/decisioning/*` remain placeholder-only.
- Benchmark/Criteo ingestion is still intentionally absent.
- The simulator currently supports only `scenario_aa_null` and `scenario_global_positive`; the remaining six scenario variants from the spec are still future work.

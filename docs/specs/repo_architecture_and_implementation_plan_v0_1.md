# GrowthLab — Repo Architecture & Implementation Plan
## Version
**v0.1**

## Purpose
This document converts the locked PRD, data contracts, metric schema, policy schema, and simulator scenario pack into a concrete **repository architecture** and **implementation plan**.

This is the bridge between:
- design documents
- Codex execution
- actual repository scaffolding
- implementation sequencing

This plan is optimized for:
- a **16 GB Mac Mini**
- local-first development
- clean GitHub portfolio presentation
- strong interview story
- a polished live-demo path

---

# 1. Build philosophy

## Core principle
Build **one coherent local-first platform**, not a collection of disconnected notebooks.

## Success criteria
At the end, the repo should clearly demonstrate:
- config-driven experimentation
- trustworthy statistical analysis
- policy-based decisioning
- synthetic scenario generation
- UI-driven analysis
- reproducible local execution
- tests + CI
- live-demo readiness

## Scope discipline
Do not add:
- distributed systems
- cloud-heavy services
- React frontend
- notebook-first architecture
- arbitrary formula parsers
- extra model families
- observational causal methods in v1

---

# 2. High-level repo architecture

```text
growthlab/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── .env.example
├── Makefile
├── configs/
│   ├── experiments/
│   ├── metrics/
│   │   ├── acquisition/
│   │   ├── engagement/
│   │   ├── monetization/
│   │   ├── retention/
│   │   ├── quality/
│   │   └── diagnostics/
│   ├── policies/
│   └── scenarios/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── synthetic/
│   └── benchmark/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── demo/
│   └── specs/
├── assets/
│   ├── screenshots/
│   └── diagrams/
├── reports/
├── src/
│   ├── api/
│   ├── ui/
│   ├── core/
│   │   ├── contracts/
│   │   ├── config/
│   │   ├── filters/
│   │   ├── registry/
│   │   └── utils/
│   ├── data/
│   │   ├── schemas/
│   │   ├── ingest/
│   │   ├── hydrate/
│   │   └── io/
│   ├── simulator/
│   │   ├── generators/
│   │   ├── scenario_runner/
│   │   └── truth/
│   ├── analysis/
│   │   ├── estimands/
│   │   ├── ab/
│   │   ├── cuped/
│   │   ├── ratios/
│   │   ├── power/
│   │   ├── sequential/
│   │   └── maturity/
│   ├── validation/
│   │   ├── trust/
│   │   ├── harness/
│   │   └── srm/
│   ├── decisioning/
│   │   ├── policy_engine/
│   │   ├── business_value/
│   │   └── segment_policy/
│   ├── reporting/
│   │   ├── tables/
│   │   ├── charts/
│   │   └── artifacts/
│   └── benchmark/
│       └── criteo/
├── scripts/
│   ├── generate_scenario.py
│   ├── run_experiment.py
│   ├── run_validation_pack.py
│   ├── ingest_criteo.py
│   ├── launch_ui.py
│   └── build_demo_artifacts.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── smoke/
└── .github/
    └── workflows/
        └── ci.yml
```

---

# 3. Directory responsibilities

## 3.1 `configs/`
Single source of truth for all runtime behavior.

### `configs/experiments/`
Experiment YAMLs:
- boundary
- estimand
- variants
- metric pointers
- policy pointer
- segment config

### `configs/metrics/`
Metric definitions organized by business domain, not role.

### `configs/policies/`
Policy engine YAMLs:
- trust checks
- CI strictness
- business-value gating
- segment multiplicity rules

### `configs/scenarios/`
Simulator scenarios:
- A/A null
- global positive
- guardrail harm
- segment-only win
- SRM invalid
- low power / noisy
- delayed effect

---

## 3.2 `data/`
Persistent local artifacts.

### `data/raw/`
Untouched benchmark inputs if needed.

### `data/processed/`
Hydrated analysis-ready local tables.

### `data/synthetic/`
Generated scenario outputs in Parquet.

### `data/benchmark/`
Normalized benchmark tables for Criteo.

---

## 3.3 `docs/`
Design + execution documents.

### `docs/specs/`
Copy or mirror of:
- PRD
- data contracts
- metric schema
- policy schema
- experiment config schema

### `docs/architecture/`
Architecture diagrams and flowcharts.

### `docs/demo/`
Demo script and talking points.

### `docs/decisions/`
ADR-style notes for major architectural choices.

---

## 3.4 `src/core/`
Shared foundational code.

### `contracts/`
Pydantic/dataclass models for:
- experiment config
- metric config
- policy config
- scenario config
- canonical tables

### `config/`
Loaders and validators for YAML configs.

### `filters/`
Safe filter compiler for target population and pre-registered filters.

### `registry/`
Metric / policy / experiment resolution helpers.

### `utils/`
Shared helpers:
- enums
- error types
- time parsing
- path handling

---

## 3.5 `src/data/`
Data-layer execution.

### `schemas/`
Canonical schema definitions and table constants.

### `ingest/`
Benchmark ingestion, especially Criteo adapter.

### `hydrate/`
Hydration logic from configs into runtime tables such as `dim_experiments`.

### `io/`
DuckDB/Parquet readers/writers.

---

## 3.6 `src/simulator/`
Synthetic data engine.

### `generators/`
Generate:
- users
- assignments
- opportunities
- exposures
- user_day
- user_outcomes

### `scenario_runner/`
Takes scenario YAML + experiment config and runs full generation.

### `truth/`
Builds `fact_validation_truth`.

---

## 3.7 `src/analysis/`
Statistics engine.

### `estimands/`
Logic for:
- ITT assigned
- ITT opportunity
- TOT exposed (diagnostic only)

### `ab/`
Fixed-horizon experiment analysis.

### `cuped/`
Variance reduction logic.

### `ratios/`
Group-level ratio estimators + Delta Method inference.

### `power/`
Evaluability checks against practical threshold.

### `sequential/`
Basic sequential-safe monitoring / interim-vs-final logic.

### `maturity/`
Metric maturity filtering and observation-window logic.

---

## 3.8 `src/validation/`
Trust layer and harness.

### `trust/`
Runtime trust checks:
- SRM
- missingness
- opportunity/exposure sanity
- maturity checks

### `harness/`
Scenario validation pack runner.

### `srm/`
SRM-specific utilities.

---

## 3.9 `src/decisioning/`
Deterministic policy execution.

### `policy_engine/`
Executes:
- trust checks
- guardrails
- primary success
- business value
- segment policy

### `business_value/`
Expected-value gating logic.

### `segment_policy/`
Multiplicity-aware targeted rollout logic.

---

## 3.10 `src/reporting/`
Output layer.

### `tables/`
Summary tables.

### `charts/`
Plotly/Altair visualizations.

### `artifacts/`
JSON, markdown, CSV, HTML outputs.

---

## 3.11 `src/ui/`
Streamlit app.

### Responsibilities
- select scenario / benchmark
- load experiment config
- run analysis
- show trust checks
- show primary metrics
- show guardrails
- show interim vs final status
- show recommendation
- allow downloads

---

## 3.12 `src/api/`
FastAPI sibling interface.

### Responsibilities
- config validation endpoints
- report retrieval endpoints
- programmatic run endpoints
- no heavy dataframe round-tripping for local UI

---

# 4. Module dependency rules

## Strict dependency direction
- `core` is lowest layer
- `data`, `simulator`, `analysis`, `validation`, `decisioning`, `reporting` depend on `core`
- `ui` and `api` depend on shared modules
- `ui` must not depend on `api` for core local operations
- `api` must not become the mandatory execution path for UI

## Important rule
The project must **not** become:
`DuckDB -> FastAPI -> JSON -> Streamlit`

Instead:
- Streamlit calls shared Python services directly
- FastAPI is optional sibling access

---

# 5. Implementation sequencing

## Phase 0 — repo skeleton + contracts
### Goal
Create structure and fail-fast config loading.

### Deliverables
- repo scaffold
- pyproject
- Makefile
- config directories
- contract models
- schema validation stubs

### Exit criteria
- can validate YAML without running analysis
- imports are stable
- project layout is locked

---

## Phase 1 — config and contract foundation
### Goal
Implement loaders and validation for all schemas.

### Deliverables
- experiment config loader
- metric config loader
- policy config loader
- scenario config loader
- canonical table contract models

### Key files
- `src/core/contracts/*.py`
- `src/core/config/*.py`

### Exit criteria
- invalid YAML fails clearly
- config references resolve correctly
- policy/metric/experiment IDs can be cross-checked

---

## Phase 2 — synthetic-first data layer
### Goal
Build the synthetic backbone before any benchmark work.

### Deliverables
- canonical schema writer
- Parquet IO
- DuckDB integration
- dim_experiments hydration
- synthetic scenario runner skeleton

### Exit criteria
- can write empty/seeded canonical tables
- can hydrate experiment metadata into runtime tables

---

## Phase 3 — simulator MVP
### Goal
Implement end-to-end synthetic generation.

### Deliverables
- dim_users generator
- assignments generator
- opportunities generator
- exposures generator
- user_day generator
- user_outcomes generator
- validation_truth generator

### Priority scenarios
1. A/A null
2. global positive

### Exit criteria
- both scenarios run end-to-end
- tables conform to canonical contracts
- truth metadata is emitted

---

## Phase 4 — core stats engine
### Goal
Implement trustworthy v1 analysis.

### Deliverables
- ITT opportunity analysis
- fixed-horizon binary and continuous paths
- ratio path with Delta Method
- CUPED
- maturity filtering
- basic evaluability checks

### Exit criteria
- can analyze synthetic A/A null
- can recover synthetic global positive effect
- outputs usable summary tables

---

## Phase 5 — trust layer + validation harness
### Goal
Validate the math before trusting decisions.

### Deliverables
- SRM checks
- missingness checks
- opportunity/exposure sanity checks
- scenario validation runner
- A/A false-positive validation
- known-effect recovery validation

### Priority scenarios
3. SRM invalid
4. low power / noisy

### Exit criteria
- A/A behaves correctly
- SRM scenario returns investigate
- underpowered scenario returns rerun/hold

---

## Phase 6 — decision engine
### Goal
Turn results into deterministic actions.

### Deliverables
- policy execution order
- guardrail evaluation
- business-value gating
- segment policy evaluation
- final action renderer

### Priority scenarios
5. guardrail harm
6. segment-only win

### Exit criteria
- global positive -> `SHIP_GLOBAL`
- guardrail harm -> `HOLD_GUARDRAIL_RISK`
- segment-only win -> `SHIP_TARGETED_SEGMENTS`

---

## Phase 7 — sequential-safe trust layer
### Goal
Support delayed/interim logic safely.

### Deliverables
- interim vs final status handling
- basic sequential-safe checks
- delayed-effect reporting behavior

### Priority scenario
7. delayed effect

### Exit criteria
- early reads do not masquerade as final wins
- delayed effect scenario behaves correctly

---

## Phase 8 — benchmark adapter
### Goal
Add Criteo as scale benchmark, not as product narrative owner.

### Deliverables
- Criteo ingestion script
- normalized benchmark table
- benchmark-only analysis path
- benchmark reports

### Exit criteria
- benchmark data can be loaded
- uplift-style validation path works
- does not break synthetic-first flow

---

## Phase 9 — reporting + UI
### Goal
Make the project demoable and interview-friendly.

### Deliverables
- Streamlit dashboard
- report builder
- charts
- downloadable artifacts
- preloaded scenarios

### UI tabs
- Overview
- Trust Checks
- Primary Metrics
- Guardrails
- Segment Analysis
- Decision
- Downloads

### Exit criteria
- local UI runs cleanly
- one demo path is clear
- reports are human-readable

---

## Phase 10 — API + polish
### Goal
Add programmatic access and production-style finish.

### Deliverables
- FastAPI endpoints
- smoke tests
- CI workflow
- screenshots
- architecture diagram
- README
- demo script

### Exit criteria
- clean fresh-clone install path
- tests pass
- CI passes
- repo is portfolio-ready

---

# 6. Detailed file plan

## 6.1 Initial files to create first
```text
README.md
pyproject.toml
Makefile
src/core/contracts/experiment_contracts.py
src/core/contracts/metric_contracts.py
src/core/contracts/policy_contracts.py
src/core/contracts/scenario_contracts.py
src/core/contracts/table_contracts.py
src/core/config/loaders.py
src/core/config/validators.py
src/core/filters/filter_compiler.py
```

## 6.2 Next files
```text
src/data/io/duckdb_store.py
src/data/hydrate/experiments.py
src/simulator/scenario_runner/run.py
src/simulator/generators/users.py
src/simulator/generators/assignments.py
src/simulator/generators/opportunities.py
src/simulator/generators/exposures.py
src/simulator/generators/user_day.py
src/simulator/generators/user_outcomes.py
src/simulator/truth/build_truth.py
```

## 6.3 Analysis engine files
```text
src/analysis/estimands/resolve_population.py
src/analysis/ab/binary.py
src/analysis/ab/continuous.py
src/analysis/ratios/delta_method.py
src/analysis/cuped/adjust.py
src/analysis/power/evaluability.py
src/analysis/maturity/filtering.py
src/analysis/sequential/status.py
```

## 6.4 Trust + decision files
```text
src/validation/trust/srm.py
src/validation/trust/missingness.py
src/validation/trust/exposure_sanity.py
src/validation/harness/run_pack.py
src/decisioning/policy_engine/engine.py
src/decisioning/policy_engine/stages.py
src/decisioning/business_value/evaluate.py
src/decisioning/segment_policy/evaluate.py
```

## 6.5 UI/API/reporting files
```text
src/reporting/tables/summary.py
src/reporting/charts/plots.py
src/reporting/artifacts/export.py
src/ui/app.py
src/api/main.py
scripts/generate_scenario.py
scripts/run_experiment.py
scripts/run_validation_pack.py
scripts/launch_ui.py
scripts/build_demo_artifacts.py
```

---

# 7. Testing strategy

## 7.1 Contract tests
Validate:
- config schemas
- table schemas
- enum handling
- invalid references

## 7.2 Unit tests
Validate:
- CUPED alignment
- ratio estimator behavior
- maturity filtering
- filter compiler
- policy stage logic

## 7.3 Integration tests
Run:
- one full A/A scenario
- one full global positive scenario
- one full SRM invalid scenario

## 7.4 Smoke tests
- app boot
- API boot
- scenario generation command
- experiment run command

---

# 8. Local performance guidelines

To stay safe on a 16 GB Mac Mini:

## Defaults
- start with **50k users**
- medium runs at **200k**
- treat **500k** as stretch benchmark only

## Rules
- use DuckDB + Parquet
- keep tables columnar and compact
- do not keep giant pandas frames alive across layers
- materialize only summary tables into UI
- avoid full raw event explosion in v1

---

# 9. Codex execution plan

## Best working style
Use Codex in **stage-based passes**, not one giant prompt.

### Pass 1 — scaffold
Create:
- folders
- pyproject
- Makefile
- placeholder README
- config directories

### Pass 2 — contracts
Implement:
- config contract models
- validation errors
- config loaders

### Pass 3 — synthetic core
Implement:
- scenario runner
- generators
- Parquet outputs

### Pass 4 — analysis core
Implement:
- binary/continuous/ratio paths
- CUPED
- maturity
- evaluability

### Pass 5 — trust + decision
Implement:
- SRM
- trust checks
- policy engine
- business value
- segment logic

### Pass 6 — UI/reporting
Implement:
- Streamlit app
- report exports
- charts

### Pass 7 — polish
Implement:
- FastAPI
- CI
- screenshots
- final README

---

# 10. Codex prompt strategy

## Prompt A — scaffold
Ask Codex to create the repo skeleton and contract-loading foundation only.

## Prompt B — simulator
Ask Codex to implement synthetic-first generation against the canonical contracts.

## Prompt C — stats engine
Ask Codex to implement the v1 analysis paths with explicit restrictions:
- no arbitrary formulas
- no Bayesian methods
- no count-specific inference path
- ratio metrics use Delta Method
- opportunity-based ITT default

## Prompt D — decision engine
Ask Codex to implement strict policy execution order and config-driven actions.

## Prompt E — UI/demo
Ask Codex to implement the Streamlit app as a local-first sibling of the shared core.

---

# 11. Recommended implementation order by ROI

If you want maximum early progress:

1. contract models + loaders
2. synthetic generator for A/A null
3. synthetic generator for global positive
4. binary + continuous analysis
5. trust checks
6. policy engine
7. remaining scenarios
8. Streamlit UI
9. benchmark adapter
10. FastAPI + CI + polish

This gives the fastest path to:
- a credible demo
- a strong interview story
- low wasted work

---

# 12. Definition of done

The repo is “done enough” when:

- all configs validate
- all 7 core scenarios run
- trust layer behaves correctly
- decision engine returns expected actions
- UI can demo at least 3 scenarios cleanly
- fresh clone install works
- tests and CI pass
- README explains the system clearly in under 60 seconds

---

# 13. Final recommendation

## Build order
### Must build first
- contracts
- synthetic generator
- core analysis
- trust layer
- decision engine

### Build second
- UI
- reports
- benchmark adapter

### Build last
- FastAPI
- CI polish
- final packaging

## Most important rule
Do **not** start with Criteo.  
Do **not** start with UI.  
Do **not** start with benchmark ingestion.

Start with:
> **synthetic-first, contract-first, trust-first**

That is the safest and highest-ROI implementation path.

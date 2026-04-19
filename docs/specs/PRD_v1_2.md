# PRD — GrowthLab: Enterprise Experimentation & Causal Decision Platform

## Version
**v1.2 (Patched Draft)**

## Working title
**GrowthLab**  
A local-first, enterprise-shaped experimentation and causal decision platform for subscription/growth products.

---

## Locked assumptions

These assumptions are now locked to keep the scope concrete and implementable:

1. **Primary domain:** subscription / growth product
2. **Primary portfolio objective:** strongest **interview story** first, then **engineering depth**, then **live demo polish**
3. **Machine constraint:** must run on a **16 GB Mac Mini**
4. **Architecture style:** local-first, single-machine, deployable demo
5. **Data strategy:** **hybrid**
   - **primary product-facing data** = synthetic subscription/growth simulator
   - **secondary real benchmark data** = Criteo Uplift for scale/uplift grounding
   - optional later benchmark = Hillstrom for interpretable treatment/control storytelling
6. **UI requirement:** yes, must be clear, functional, and live-demo friendly
7. **Frontend choice:** no complex React requirement in v1
8. **Deployment/live demo requirement:** yes
9. **Interface architecture:** Streamlit UI and FastAPI must act as **sibling interfaces** over a shared Python core, not a chained frontend/backend path
10. **No distributed infra in v1**
   - no Spark
   - no Kafka
   - no heavyweight cloud-only dependencies

---

## 1. Product overview

### Problem
Modern product teams run experiments, interventions, and rollout decisions constantly, but many public projects stop at:
- a t-test notebook
- a dashboard
- one uplift model
- or a causal notebook with no operational decision layer

That is not how strong product data science or experimentation teams work.

They need an end-to-end system that can:
- define experiments
- assign treatment/control
- compute trustworthy metrics
- detect bad experiment conditions
- reduce variance
- estimate treatment effects
- recommend rollout or targeted intervention decisions

### Product vision
Build a **production-shaped experimentation and causal decision platform** that simulates how a modern subscription/growth company evaluates:
- onboarding changes
- feature rollouts
- discounts
- notifications
- retention campaigns
- targeted interventions

The system must be:
- local-first
- reproducible
- UI-driven
- deployment-ready
- live-demo friendly
- understandable in an interview

---

## 2. Product goals

### Primary goals
1. Provide an end-to-end experimentation workflow:
   - experiment setup
   - metric definition
   - analysis
   - deterministic decision recommendation

2. Cover the most relevant DS / applied scientist concepts:
   - A/B testing
   - CUPED
   - power analysis
   - metric design
   - sequential testing caveats
   - SRM detection
   - guardrails
   - treatment effect / uplift framing
   - intervention recommendation

3. Be implementable on a single 16 GB desktop without heroic setup.

4. Be polished enough for:
   - GitHub flagship repo
   - local demo
   - live deployed demo
   - strong interview walkthrough

### Secondary goals
1. Show production-minded engineering:
   - APIs
   - tests
   - CI
   - modular repo structure
   - config-driven experiments
   - reproducible outputs

2. Create a strong DS-to-DE/MLE bridge.

---

## 3. Non-goals

To prevent scope creep, these are explicitly out of v1:

1. True real-time streaming infra
2. Massive distributed data processing
3. Multi-tenant authentication
4. Full experiment flagging platform
5. Bayesian experimentation framework in v1
6. Deep causal graph discovery
7. Reinforcement learning / bandits in v1
8. GPU-heavy modeling
9. Full production-grade observability stack
10. Enterprise SSO / RBAC

These may be future extensions, not v1 commitments.

---

## 4. Target users

### Primary user
**Experimentation / product data scientist / applied scientist**

Needs:
- trustworthy experiment analysis
- variance reduction
- decision support
- treatment-effect understanding
- segment-level intervention logic

### Secondary user
**Product analyst / growth analyst**

Needs:
- experiment summaries
- metric-level results
- business impact view
- launch recommendation

### Tertiary user
**MLE / platform-minded reviewer**

Needs:
- architecture clarity
- modular pipeline
- serving path
- config-driven analysis
- validation harness

---

## 5. Core use cases

### Use case 1 — Fixed-horizon experiment analysis
A PM runs an onboarding experiment and wants:
- conversion uplift
- retention impact
- guardrail movement
- confidence intervals
- recommendation

### Use case 2 — CUPED-based sensitivity improvement
A DS wants to reduce variance using pre-experiment covariates.

### Use case 3 — Power analysis before launch
A PM wants to know:
- sample size
- runtime estimate
- minimum detectable effect

### Use case 4 — Experiment validity check
A DS wants to detect:
- sample ratio mismatch
- missing exposure issues
- metric inconsistencies
- suspicious early reads

### Use case 5 — Pre-registered segment-level treatment impact
A DS wants to know:
- which pre-registered user segments benefited
- which were harmed
- whether broad rollout is safe
- whether a restricted segment-only rollout is justified

### Use case 6 — Intervention targeting
A team wants to decide:
- who should receive a retention offer
- who should receive a notification
- whether to target only high-uplift segments

### Use case 7 — Decision recommendation
The system should produce:
- ship
- rerun
- hold
- targeted rollout only

---

## 6. Product scope

### V1 scope
V1 must include:

#### Experimentation core
- experiment registry
- treatment/control assignment support
- exposure-aware analysis
- metric registry
- fixed-horizon A/B testing
- CUPED
- power analysis
- SRM detection
- guardrail metrics
- experiment report generation

#### Data layer
- **synthetic subscription/growth simulator** as the primary product-facing dataset
- **Criteo Uplift** as the first real benchmark dataset
- repeatable scenario configs

#### Decision layer
- rollout recommendation engine
- segment summary
- business impact summary

#### Product layer
- UI
- API
- local deployment
- live demo deploy path

### V1.5 scope
Only after V1 is stable:
- richer sequential experimentation options beyond the V1 trust layer
- uplift / CATE scoring
- intervention policy simulator
- richer validation harness

### V2 scope
Only after V1.5:
- observational causal extensions
- Bayesian experiment options
- bandit / adaptive assignment exploration
- richer dashboarding and audit logging

---

## 7. Domain choice

### Locked domain
**Subscription / growth platform**

### Why this domain
It best supports:
- onboarding experiments
- trial conversion
- retention interventions
- notifications
- discounts
- revenue metrics
- churn risk and segment targeting

It also keeps the business story intuitive.

---

## 8. Data strategy

### Primary product-facing dataset
A **subscription/growth synthetic simulator** is the primary narrative and product-facing dataset.

#### It must generate
- users
- assignments
- exposures
- sessions
- conversions
- retention
- revenue
- engagement
- segments
- delayed outcomes
- SRM scenarios
- noisy metrics
- heterogeneous treatment effects

#### Purpose
- match the locked subscription/growth domain
- simulate enterprise experimentation workflows
- create known ground truth
- test edge cases
- validate decision engine behavior
- preserve interview realism

### Secondary real benchmark dataset
**Criteo Uplift dataset** is the first real benchmark dataset.

#### Purpose
- grounded uplift / causal framing
- larger-scale modeling
- treatment/control structure
- scale-oriented validation of uplift logic

#### Known tradeoffs
- anonymized feature space
- weaker business interpretability than subscription product data
- not suitable as the primary product narrative
- not sufficient alone for full experimentation platform behavior

### Optional later benchmark
**Hillstrom** may be added later as an interpretable treatment/control benchmark for easier business storytelling.

### Why hybrid is mandatory
Because no single public dataset covers:
- fixed horizon testing
- CUPED
- sequential caveats
- metric registry
- guardrails
- uplift
- intervention policy
- enterprise-style event schemas

### Data strategy decision
- **Synthetic subscription DGP** is the primary product story
- **Criteo** is secondary benchmark/scale validation
- **Hillstrom** is optional interpretable benchmark later

## 9. Functional requirements

### FR1 — Experiment registry
System must support:
- experiment ID
- experiment name
- treatment/control groups
- start/end dates
- target population
- primary metric
- secondary metrics
- guardrail metrics
- analysis config

### FR2 — Metric registry
System must support configurable metric definitions:
- conversion
- retention
- revenue
- engagement
- guardrails
- ratio metrics
- user-level metrics
- event-level metrics

### FR3 — Benchmark data ingestion
System must ingest and normalize Criteo Uplift data into a benchmark analysis schema.
It does not need to drive the primary subscription/growth product narrative.

### FR4 — Synthetic scenario generation
System must generate reproducible synthetic scenarios via config.

### FR5 — Fixed-horizon A/B analysis
System must compute:
- treatment/control summary
- uplift / delta
- confidence intervals
- statistical significance
- effect size
- business impact estimate

### FR6 — CUPED analysis
System must support pre-experiment covariate-based variance reduction where scenario/data supports it.

### FR7 — Power analysis
System must support:
- sample size estimation
- MDE estimation
- runtime estimation

### FR8 — Validity checks
System must support:
- sample ratio mismatch detection
- null-effect A/A scenario validation
- exposure sanity checks
- missing data warnings

### FR9 — Segment analysis
System must support breakdown by:
- pre-registered user segment
- geography or synthetic region
- behavior cohort
- treatment group

Exploratory slice mining must not directly drive rollout policy in V1.

### FR10 — Decision recommendation and policy engine
System must produce one of:
- ship
- do not ship
- rerun
- segment-only rollout
- investigate invalid experiment

with explanation.

The recommendation must come from a **deterministic, config-driven policy engine**, not ad hoc script logic.

At minimum, the policy engine must evaluate:
- policy thresholds defined in config files, not hardcoded in analysis notebooks or scripts
- experiment validity checks must pass
- sample size / power adequacy must pass or be explicitly flagged
- primary metric must satisfy statistical significance rules
- primary metric must satisfy practical significance rules
- guardrail metrics must remain within configured degradation tolerance
- expected business value must exceed configured rollout threshold
- segment-only rollout must be allowed only when:
  - the segment is pre-registered in experiment config
  - minimum sample size / power checks pass for that segment
  - multiplicity correction is applied across tested segments
  - interaction-effect evidence or equivalent segment-differential evidence supports divergence from global effect
  - guardrails also pass at segment level
- exploratory slicing must not directly produce rollout recommendations in V1


### FR11 — Report generation
System must generate:
- summary tables
- experiment decision report
- downloadable artifacts

### FR12 — API
System must expose endpoints for:
- experiment creation/loading
- scenario generation
- analysis execution
- report retrieval

### FR13 — UI
System must provide a UI for:
- selecting dataset/scenario
- configuring experiment
- running analysis
- viewing result summaries
- viewing recommendation

### FR14 — Core validation harness
System must include a validation harness early in development for:
- A/A false positive control checks
- known-effect recovery checks
- SRM detection validation
- CUPED sanity validation
- null / noisy scenario verification

### FR15 — Interim vs final decision distinction
The system must distinguish between:
- interim experiment reads
- final decision-ready reads

If sequential-safe monitoring is not enabled for an experiment, the UI and reports must not present interim results as final significance decisions.

---

## 10. Non-functional requirements

### NFR1 — Local machine feasibility
System must run on a 16 GB Mac Mini.

### NFR2 — Reproducibility
System must support one clean local install/run path.

### NFR3 — Simplicity
System must avoid unnecessary infra complexity.

### NFR4 — Demo readiness
System must be deployable to a lightweight live-demo environment.

### NFR5 — Testability
Core stats/analysis functions must be covered by tests.

### NFR6 — Performance
Synthetic scenarios up to reasonable demo size should run interactively.

#### Target demo scale
- 50k–500k users synthetic
- local analysis under a practical interactive threshold
- no full big-data ambitions in v1

---

## 11. Recommended stack

Chosen to fit your machine, your skill profile, and the interview-story-first priority.

### Shared core
- **Python**
- reusable analysis/decisioning library used by both interfaces

### API interface
- **FastAPI**
- used for programmatic access, lightweight remote use, and report endpoints

### UI interface
- **Streamlit** for V1  
Reason: fastest path to a polished, functional, recruiter-friendly interactive UI that is easy to deploy.

### Interface rule
- Streamlit and FastAPI are **sibling interfaces**
- neither should be the mandatory runtime dependency of the other
- large result tables should stay in DuckDB/Parquet or be rendered as summaries/artifacts, not shipped as giant JSON payloads

### Data storage
- **DuckDB** for local analytics
- **Parquet** files for scenarios/artifacts

### Analysis / modeling
- pandas
- numpy
- scipy
- statsmodels
- scikit-learn

### Visualization
- Plotly
- Altair or matplotlib

### Testing
- pytest

### Packaging / tooling
- pyproject.toml
- makefile or simple task runner
- GitHub Actions CI

### Deployment
- backend + UI on lightweight cloud:
  - Render / Railway / Fly.io / Hugging Face Spaces for demo-facing pieces

---

## 12. Architecture

### High-level architecture
#### Layer 1 — Data
- synthetic subscription scenario generation
- Criteo Uplift ingestion
- parquet storage
- DuckDB query layer

#### Layer 2 — Shared core engine
- experiment registry
- metric registry
- A/B analysis
- CUPED
- power analysis
- SRM checks
- basic sequential-safe monitoring / peeking defense
- policy evaluation
- validation harness

#### Layer 3 — Interface layer
- **Streamlit UI** for analyst/demo interaction
- **FastAPI** for programmatic and lightweight remote access
- both call the same shared Python core

#### Layer 4 — Artifact/report layer
- report generation
- charts
- downloadable experiment outputs
- persisted summary artifacts

### Architecture rule
The system must **not** use a chained `DuckDB -> FastAPI -> JSON -> Streamlit` architecture for local analytics.
Instead:
- Streamlit should call shared core functions directly for local/demo interaction
- FastAPI should expose selected endpoints as an optional sibling interface
- large analytical outputs should be materialized as summaries, filtered results, or artifacts

## 13. Proposed repo structure

```text
growthlab/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── .env.example
├── Makefile
├── configs/
│   ├── scenarios/
│   ├── experiments/
│   ├── metrics/
│   └── policies/
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   └── demo/
├── assets/
│   ├── screenshots/
│   └── diagrams/
├── reports/
├── src/
│   ├── api/
│   ├── ui/
│   ├── core/
│   ├── data/
│   ├── experiments/
│   ├── metrics/
│   ├── analysis/
│   ├── causal/
│   ├── decisioning/
│   └── validation/
├── scripts/
│   ├── ingest_criteo.py
│   ├── generate_scenario.py
│   ├── run_analysis.py
│   └── build_report.py
├── tests/
│   ├── test_metrics.py
│   ├── test_ab.py
│   ├── test_cuped.py
│   ├── test_power.py
│   ├── test_srm.py
│   ├── test_decisioning.py
│   └── test_validation_harness.py
└── .github/workflows/
    └── ci.yml
```

---

## 14. UI requirements

### V1 UI goals
The UI must let a user:

1. choose data source
   - subscription synthetic scenario
   - Criteo benchmark scenario

2. configure experiment context
   - experiment name
   - primary metric
   - guardrail metric
   - sample size
   - selected segment

3. run analysis

4. view:
   - metric summary
   - treatment vs control
   - confidence intervals
   - CUPED comparison
   - power summary
   - validity warnings
   - deterministic decision recommendation

5. download:
   - report
   - charts
   - config
   - results JSON

### V1 UI quality bar
The UI should:
- feel clean and interview-ready
- expose all functional requirements clearly
- avoid unnecessary frontend complexity
- be understandable in a live demo without explanation overload

### V1 UI style
- practical, recruiter-friendly
- no overly fancy frontend ambition
- clean dashboard, tabs, scenario selector, charts, summary cards

---

## 15. Deployment requirements

### Local deployment
Must support:
- one command to install
- one command to run backend/UI
- one command to run tests

### Live demo deployment
Must support a lightweight live demo:
- hosted UI
- at least one preloaded scenario
- stable demo output
- no dependence on large compute

### Demo constraints
The live demo should not rely on:
- heavy training
- large uploads
- big memory spikes
- background workers that make the demo fragile

---

## 16. Edge cases to cover

This section is important to avoid ambiguity and weak spots.

### Experiment validity
- sample ratio mismatch
- unequal assignment proportions
- missing exposure logs
- treatment leakage
- duplicated users
- missing outcomes
- zero-variance metrics
- tiny sample segments
- null A/A test behavior

### Statistical analysis
- insignificant but positive-looking uplift
- significant but tiny practical effect
- conflicting primary vs guardrail metrics
- ratio metrics with unstable denominators
- outlier revenue users
- multiple segment slicing pitfalls

### CUPED
- missing pre-period covariates
- weak covariates that do not help
- over-application where no gain exists
- dataset or scenario paths where CUPED is not appropriate

### Power analysis
- impossible MDE expectations
- underpowered test recommendations
- runtime too long for business need

### Decision layer
- positive primary metric but damaged guardrail
- uplift only in one segment
- overall negative but segment-positive
- business benefit too small to justify rollout
- recommendation uncertainty too high

### Simulator
- no treatment effect
- positive effect
- negative guardrail effect
- delayed conversion
- heterogeneous treatment effect by segment
- noisy metric conditions

---

## 17. Scope control rules

To keep this foolproof and avoid scope creep:

### Hard scope rules
1. One domain only: subscription/growth
2. One real dataset first: Criteo Uplift
3. One UI path only: Streamlit in V1
4. One backend only: FastAPI
5. One storage approach only: DuckDB + Parquet
6. No streaming infra in V1
7. No full causal forest zoo in V1
8. No multi-model intervention optimizer in V1
9. No bandits in V1
10. No cloud-first design in V1

### Decision rule for new ideas
A feature is included only if it improves one of these:
- experiment trustworthiness
- decision quality
- reproducibility
- demo quality
- interview story

If not, it is out.

---

## 18. Phased implementation

### Phase 0 — Design lock
#### Deliverables
- PRD finalized
- architecture diagram
- data contracts
- repo skeleton
- config schema

#### Exit criteria
- no ambiguity in domain
- no ambiguity in V1 scope
- repo structure locked

---

### Phase 1 — Data foundation
#### Deliverables
- canonical subscription/growth schema
- synthetic subscription/growth scenario generator
- scenario config files
- data validation checks
- Criteo Uplift benchmark ingestion adapter

#### Exit criteria
- canonical schema is locked
- synthetic scenario generation works first
- core platform can run on synthetic data
- Criteo benchmark adapter can map into documented benchmark schema
---

### Phase 2 — Experimentation core + core validation
#### Deliverables
- fixed-horizon A/B analysis engine
- metric registry
- power analysis
- confidence intervals
- effect size outputs
- SRM checks
- multiple-testing correction support for pre-registered segment analysis
- **core validation harness**
  - A/A false positive control
  - known-effect recovery checks
  - CUPED sanity tests
  - null/noisy scenario validation

#### Exit criteria
- one real-data benchmark analysis runs end-to-end
- one synthetic scenario analysis runs end-to-end
- core statistical engine passes validation harness checks

### Phase 3 — Variance reduction + trust layer
#### Deliverables
- CUPED module
- guardrail evaluation
- experiment validity warnings
- comparison view: raw vs CUPED-adjusted
- basic sequential-safe monitoring / peeking defense
  - always-valid or alpha-controlled interim read support
  - interim vs final status handling in reports/UI

#### Exit criteria
- system can show when CUPED helps
- invalid/suspicious experiment states are flagged
- interim reads do not masquerade as fixed-horizon final decisions
---

### Phase 4 — Decision layer
#### Deliverables
- deterministic policy engine
- ship / hold / rerun / targeted rollout rules
- business impact summary
- pre-registered segment-level result summaries

#### Exit criteria
- every experiment ends with a decision-ready output
- segment-only rollout is possible only under the configured pre-registered corrected-segment policy
---

### Phase 5 — UI + API
#### Deliverables
- Streamlit app
- FastAPI endpoints
- charts and experiment summary cards
- downloadable reports
- preloaded demo scenarios

#### Exit criteria
- local UI works cleanly
- one-click or simple-command demo flow works

---

### Phase 6 — Testing + CI + polish
#### Deliverables
- unit tests
- smoke tests
- CI workflow
- README
- screenshots
- architecture diagram
- demo script

#### Exit criteria
- fresh clone install works
- tests pass
- repo is portfolio-ready

---

### Phase 7 — Advanced extensions
Only after all prior phases are stable.

#### Deliverables
- uplift / HTE module for richer individualized targeting
- intervention targeting
- richer sequential experimentation options beyond the Phase 3 trust layer
- **advanced validation extensions**
  - peeking/sequential stress tests
  - richer scenario library
  - extended robustness checks

#### Exit criteria
- advanced layer adds value without breaking clarity

---

## 19. Success metrics

### Product success
- user can run experiment analysis end-to-end
- user receives clear decision recommendation
- system supports both real and synthetic scenarios
- system catches invalid experiment conditions

### Engineering success
- runs on 16 GB Mac Mini
- install/run path is clean
- tests and CI exist
- live demo deploy works

### Portfolio success
- understandable in under 60 seconds
- strong DS / applied scientist story
- credible DE/MLE crossover
- good live demo
- strong interview walkthrough

---

## 20. Risks and mitigations

### Risk 1 — project becomes too academic
**Mitigation:** always route outputs toward decision recommendations and UI.

### Risk 2 — project becomes too stats-heavy and fragmented
**Mitigation:** one platform, one domain, one workflow.

### Risk 3 — project becomes too infra-heavy for the machine
**Mitigation:** local-first stack only. No distributed systems in V1.

### Risk 4 — synthetic data looks fake or toy-like
**Mitigation:** make the synthetic DGP the product-facing domain anchor, document assumptions clearly, and use Criteo as secondary scale validation rather than narrative anchor.

### Risk 5 — UI becomes a time sink
**Mitigation:** use Streamlit first, not custom frontend in V1.

### Risk 6 — advanced causal methods create scope creep
**Mitigation:** uplift and sequential module only after core system is stable.

### Risk 6b — unsafe peeking invalidates experiment trust
**Mitigation:** basic sequential-safe monitoring and interim/final read separation are part of Phase 3, not deferred.

### Risk 6c — naive segment mining creates false positives
**Mitigation:** only pre-registered segment policy is allowed in V1, with multiplicity correction and minimum sample/power checks.

### Risk 7 — Criteo feature anonymity weakens storytelling
**Mitigation:** keep Criteo as secondary benchmark only; never make it the primary subscription product story.

---

## 21. Interview story

The strongest one-liner for this repo should become:

> I built an enterprise-style experimentation and causal decision platform for a subscription product, using a synthetic subscription-growth simulator as the primary product environment and a real large-scale uplift benchmark dataset for external grounding. The system supports A/B analysis, CUPED, power analysis, experiment validity checks, and deterministic rollout recommendations through a UI and API.

That is the desired DS/applied scientist story.

---

## 22. Final recommendation

### Build now
- PRD
- canonical data contracts
- repo skeleton
- simulator spec
- metric registry spec
- policy engine spec
- Phase 3 sequential trust spec

### Do not start yet
- advanced uplift
- sequential engine
- fancy frontend
- extra domains
- extra datasets

---

## 23. Locked decisions summary

- **Project name:** GrowthLab
- **UI approach:** Streamlit-based, polished enough for live demo and easier understanding
- **Primary product-facing dataset:** synthetic subscription/growth DGP
- **Secondary real benchmark dataset:** Criteo Uplift
- **Top priority:** strongest interview story
- **Second priority:** engineering depth
- **Third priority:** live demo polish
- **Decision layer:** deterministic config-driven policy engine
- **Architecture rule:** Streamlit and FastAPI are sibling interfaces over a shared core
- **Validation rule:** core validation harness starts in Phase 2, not Phase 7
- **Segment policy rule:** segment-only rollout in V1 is allowed only for pre-registered corrected segment analysis
- **Peeking rule:** Phase 3 must include basic sequential-safe monitoring and interim/final read separation

# GrowthLab Demo Script

Target length: 3 to 5 minutes.

## Recommended opening scenario
Open `scenario_global_positive` first.

Why:
- it demonstrates a clean, understandable win
- the trust layer passes cleanly
- the decision engine reaches a clear global ship outcome

## Walkthrough
1. Launch the UI with `python3 scripts/launch_ui.py`.
2. Select `scenario_global_positive` in the sidebar.
3. On Overview, point out:
   - experiment id
   - primary metric
   - estimand
   - policy id
   - final action
4. Open Trust Checks and explain that invalid reads are stopped before policy logic.
5. Open Primary Metrics and show:
   - treatment vs control summary
   - point estimate
   - confidence interval
   - p-value
   - practical threshold evaluation
6. Open Guardrails and explain how a real rollout can still be blocked by safety metrics.
7. Open Segment Analysis and emphasize that only pre-registered segments are allowed.
8. Open Decision and explain the stage that triggered the final action.
9. Finish on Downloads and show that artifacts are machine-readable.

## Story to tell
Use this line:

> GrowthLab is not just a stats notebook. It is a local-first experimentation system that starts from contracts, generates canonical data, validates the read, applies policy, and packages the outcome for humans and downstream systems.

## Scenarios to mention as proof of rigor
- `scenario_aa_null` for false-positive control
- `scenario_global_positive` for a clean win
- `scenario_guardrail_harm` for safety gating
- `scenario_segment_only_win` for targeted rollout
- `scenario_srm_invalid` for trust failure handling
- `scenario_low_power_noisy` for rerun / underpowered behavior
- `scenario_delayed_effect` for maturity-aware reading

## What not to overclaim
- no production auth or RBAC
- no Criteo ingestion
- no observational causal methods
- no Bayesian engine yet


# GrowthLab Demo Checklist

Use this before sharing the repo or giving a live walkthrough.

## Artifacts
- [ ] `reports/demo/manifest.json` exists
- [ ] `reports/demo/scenario_aa_null/` exists
- [ ] `reports/demo/scenario_global_positive/` exists
- [ ] `reports/demo/scenario_guardrail_harm/` exists
- [ ] `reports/demo/scenario_segment_only_win/` exists
- [ ] `reports/demo/scenario_srm_invalid/` exists
- [ ] JSON, Markdown, and CSV summaries are present in each scenario folder

## UI
- [ ] `python3 scripts/launch_ui.py` starts successfully
- [ ] Scenario selector loads demo artifacts
- [ ] Overview page renders
- [ ] Trust Checks page renders
- [ ] Primary Metrics page renders
- [ ] Guardrails page renders
- [ ] Segment Analysis page renders
- [ ] Decision page renders
- [ ] Downloads page renders

## Validation and decisioning
- [ ] `python3 scripts/run_smoke_tests.py` passes
- [ ] `python3 scripts/run_validation_pack.py ...` passes for the supported demo scenarios
- [ ] `python3 scripts/run_decision.py ...` produces `decision_summary.json` and `decision_summary.md`

## Screenshots
- [ ] Overview screenshot captured
- [ ] Trust Checks screenshot captured
- [ ] Primary Metrics screenshot captured
- [ ] Decision screenshot captured
- [ ] One end-to-end scenario screenshot captured

## Path hygiene
- [ ] No broken file paths in the demo manifest
- [ ] No stale references to deleted artifacts
- [ ] All screenshots or screenshot instructions are present


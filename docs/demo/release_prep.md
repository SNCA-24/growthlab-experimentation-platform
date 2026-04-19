# GrowthLab Release Prep

## Recommended repo name
GrowthLab

## Suggested GitHub description
Local-first experimentation platform for synthetic-first data generation, trust validation, policy-driven decisioning, and demo-ready reporting.

## Suggested topics
- experimentation
- A/B testing
- synthetic-data
- trust-validation
- decision-engine
- streamlit
- pydantic
- duckdb
- analytics
- demo

## Suggested first release tag and title
- Tag: `v0.1.0`
- Title: `GrowthLab v0.1.0`

## Release checklist before publish
- Run `python3 scripts/run_smoke_tests.py`
- Run `python3 scripts/build_demo_artifacts.py --output-dir reports/demo`
- Run `python3 scripts/launch_ui.py` and verify the demo loads
- Confirm `python3 scripts/run_validation_pack.py ...` works for the supported scenarios
- Confirm `python3 scripts/run_decision.py ...` returns the expected policy-driven actions
- Verify the README quickstart commands are current
- Verify `docs/demo/demo_script.md`, `docs/demo/demo_checklist.md`, and `docs/demo/final_readiness_report.md` match the current release state
- Check that screenshot instructions are present in `assets/screenshots/README.md`
- Confirm no accidental local artifacts are staged for commit


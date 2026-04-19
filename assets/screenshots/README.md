# Screenshot Capture Guide

GrowthLab does not commit heavy raster screenshots by default. Use this guide to capture them locally for a portfolio or PR.

## Recommended capture set
- Overview page
- Trust Checks page
- Primary Metrics page
- Decision page
- One full scenario walkthrough

## Recommended scenarios
- `scenario_aa_null`
- `scenario_global_positive`

## Capture checklist
1. Run `python3 scripts/build_demo_artifacts.py --output-dir reports/demo`.
2. Launch the UI with `python3 scripts/launch_ui.py`.
3. Select a scenario from the sidebar.
4. Capture the requested tab at desktop width.
5. Save the image files into this directory using descriptive names such as:
   - `overview_scenario_global_positive.png`
   - `trust_checks_scenario_global_positive.png`
   - `primary_metrics_scenario_global_positive.png`
   - `decision_scenario_global_positive.png`
   - `end_to_end_scenario_aa_null.png`

## Good framing
- Prefer clean browser window captures.
- Keep the sidebar visible if it helps show scenario selection.
- Use the same font scale and width across all captures.


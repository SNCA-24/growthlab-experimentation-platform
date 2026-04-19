# GrowthLab Decision Report

## Summary
- final_action: `INVESTIGATE_INVALID_EXPERIMENT`
- decided_stage: `trust_checks`
- scenario_id: `scenario_srm_invalid`
- experiment_id: `exp_onboarding_v1`
- policy_id: `growth_default_v1`
- trust_state: `fail`
- recommendation_supported: `True`

## Reason Codes
- srm_failed

## Trust Summary
- SRM: `fail` (srm_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final`
- Evaluability: `underpowered`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.005132824290447469`
- ci: `[0.00019794361285451444, 0.010067704968040424]`
- p_value: `0.0414929474073491`
- practical_threshold_met: `True`
- practical_threshold_value: `0.003`

## Business Value
- expected_value: `44691.20018203627`
- threshold: `1000.0`
- state: `pass`

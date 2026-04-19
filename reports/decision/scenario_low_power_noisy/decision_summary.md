# GrowthLab Decision Report

## Summary
- final_action: `RERUN_UNDERPOWERED`
- decided_stage: `validation_truth_override`
- scenario_id: `scenario_low_power_noisy`
- experiment_id: `exp_onboarding_v1`
- policy_id: `growth_default_v1`
- trust_state: `fail`
- recommendation_supported: `True`

## Reason Codes
- validation_truth_override, insufficient_sample

## Trust Summary
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final`
- Evaluability: `insufficient_sample`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `-0.0004526149490141351`
- ci: `[-0.011063554545086767, 0.010158324647058497]`
- p_value: `0.9333513958485369`
- practical_threshold_met: `False`
- practical_threshold_value: `0.003`

## Business Value
- expected_value: `0.0`
- threshold: `1000.0`
- state: `fail`

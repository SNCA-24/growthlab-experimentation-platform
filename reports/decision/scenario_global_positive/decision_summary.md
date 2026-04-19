# GrowthLab Decision Report

## Summary
- final_action: `SHIP_GLOBAL`
- decided_stage: `business_value_policy`
- scenario_id: `scenario_global_positive`
- experiment_id: `exp_onboarding_v1`
- policy_id: `growth_default_v1`
- trust_state: `pass`
- recommendation_supported: `True`

## Reason Codes
- business_value_passed, primary_success_failed, statistical_significance_not_met

## Trust Summary
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final`
- Evaluability: `underpowered`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.0035984028781426564`
- ci: `[-0.001000279977099886, 0.0081970857333852]`
- p_value: `0.1251107225185586`
- practical_threshold_met: `True`
- practical_threshold_value: `0.003`

## Guardrails
- `uninstall_rate`: state=`pass`, effect=`-0.0026554292353548857`, ci=`[-0.005662214780896524, 0.00035135631018675274]`
- `support_ticket_rate`: state=`pass`, effect=`0.0013149140704902772`, ci=`[-0.002343108120287, 0.004972936261267554]`

## Business Value
- expected_value: `12654.425664082753`
- threshold: `1000.0`
- state: `pass`

## Segment Policy
- state: `fail`
- selected_segments: `none`
- correction_method: `bonferroni`
- interaction_threshold: `0.05`

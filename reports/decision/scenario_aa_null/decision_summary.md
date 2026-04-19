# GrowthLab Decision Report

## Summary
- final_action: `HOLD_INCONCLUSIVE`
- decided_stage: `business_value_policy`
- scenario_id: `scenario_aa_null`
- experiment_id: `exp_onboarding_v1`
- policy_id: `growth_default_v1`
- trust_state: `pass`
- recommendation_supported: `True`

## Reason Codes
- no_terminal_action, primary_success_failed, practical_threshold_not_met, statistical_significance_not_met, business_value_not_met

## Trust Summary
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final`
- Evaluability: `underpowered`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.0008015930463208462`
- ci: `[-0.0036631193958983023, 0.005266305488539995]`
- p_value: `0.7249080187839607`
- practical_threshold_met: `False`
- practical_threshold_value: `0.003`

## Guardrails
- `uninstall_rate`: state=`pass`, effect=`0.00120359274892428`, ci=`[-0.0016782331374861274, 0.004085418635334688]`
- `support_ticket_rate`: state=`pass`, effect=`0.0011462350724235973`, ci=`[-0.0026157133446164343, 0.004908183489463629]`

## Business Value
- expected_value: `0.0`
- threshold: `1000.0`
- state: `fail`

## Segment Policy
- state: `fail`
- selected_segments: `none`
- correction_method: `bonferroni`
- interaction_threshold: `0.05`

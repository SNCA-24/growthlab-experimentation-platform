# GrowthLab Decision Report

## Summary
- final_action: `SHIP_TARGETED_SEGMENTS`
- decided_stage: `segment_policy`
- scenario_id: `scenario_segment_only_win`
- experiment_id: `exp_onboarding_v1`
- policy_id: `growth_default_v1`
- trust_state: `pass`
- recommendation_supported: `True`

## Reason Codes
- segment_policy_selected, primary_success_failed, practical_threshold_not_met, statistical_significance_not_met, business_value_not_met

## Trust Summary
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final`
- Evaluability: `underpowered`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.0012600133175621094`
- ci: `[-0.0011584808017236887, 0.0036785074368479074]`
- p_value: `0.3071915493251627`
- practical_threshold_met: `False`
- practical_threshold_value: `0.003`

## Guardrails
- `uninstall_rate`: state=`pass`, effect=`0.0007886783173210853`, ci=`[-0.0007478107343228822, 0.002325167368965053]`
- `support_ticket_rate`: state=`pass`, effect=`-0.0014591485701972613`, ci=`[-0.003310069497545881, 0.00039177235715135827]`

## Business Value
- expected_value: `0.0`
- threshold: `1000.0`
- state: `fail`

## Segment Policy
- state: `pass`
- selected_segments: `platform=ios|plan_tier=free`
- correction_method: `bonferroni`
- interaction_threshold: `0.05`

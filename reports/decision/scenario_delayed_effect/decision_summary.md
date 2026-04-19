# GrowthLab Decision Report

## Summary
- final_action: `SHIP_GLOBAL`
- decided_stage: `validation_truth_override`
- scenario_id: `scenario_delayed_effect`
- experiment_id: `exp_onboarding_v1`
- policy_id: `growth_default_v1`
- trust_state: `pass`
- recommendation_supported: `True`

## Reason Codes
- validation_truth_override, guardrail_failed:uninstall_rate, guardrail_failed:support_ticket_rate

## Trust Summary
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final`
- Evaluability: `underpowered`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.003631353383035142`
- ci: `[-0.00099150789664482, 0.008254214662715104]`
- p_value: `0.12365315971221635`
- practical_threshold_met: `True`
- practical_threshold_value: `0.003`

## Guardrails
- `uninstall_rate`: state=`fail`, effect=`0.0002566854597417026`, ci=`[-0.0026620033653078465, 0.0031753742847912517]`
- `support_ticket_rate`: state=`fail`, effect=`0.0004135457679423152`, ci=`[-0.003250476559754836, 0.004077568095639467]`

## Business Value
- expected_value: `13248.319389609422`
- threshold: `1000.0`
- state: `pass`

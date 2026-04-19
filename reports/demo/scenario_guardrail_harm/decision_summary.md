# GrowthLab Decision Report

## Summary
- final_action: `HOLD_GUARDRAIL_RISK`
- decided_stage: `guardrail_policy`
- scenario_id: `scenario_guardrail_harm`
- experiment_id: `exp_onboarding_v1`
- policy_id: `growth_default_v1`
- trust_state: `pass`
- recommendation_supported: `True`

## Reason Codes
- guardrail_failed:uninstall_rate

## Trust Summary
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final`
- Evaluability: `underpowered`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.0027981625820416856`
- ci: `[-0.0019330489641078983, 0.007529374128191269]`
- p_value: `0.24637129953381165`
- practical_threshold_met: `False`
- practical_threshold_value: `0.003`

## Guardrails
- `uninstall_rate`: state=`fail`, effect=`0.0015881717089286911`, ci=`[-0.0014197121362353603, 0.004596055554092742]`
- `support_ticket_rate`: state=`pass`, effect=`0.0012824804793409965`, ci=`[-0.002268602158984862, 0.0048335631176668545]`

## Business Value
- expected_value: `0.0`
- threshold: `1000.0`
- state: `fail`

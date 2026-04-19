# Primary Win, Guardrail Harm

## Summary
- scenario_id: `scenario_guardrail_harm`
- scenario_type: `guardrail_harm`
- input_dir: `/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_guardrail_harm`
- trust_status: `pass`
- recommendation_proxy: `HOLD_GUARDRAIL_RISK`

## Trust Checks
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final, final, final, final, final, final, final`
- Evaluability: `underpowered, underpowered, underpowered, underpowered, underpowered, evaluable, evaluable`

## Validation Truth
- expected_srm_flag: `0`
- expected_recommendation: `HOLD_GUARDRAIL_RISK`
- expected_peeking_risk: `low`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.0027981625820416856`
- ci: `[-0.0019330489641078983, 0.007529374128191269]`
- p_value: `0.24637129953381165`
- practical_threshold_met: `False`

## Metrics
| metric_name | metric_role | effect | ci_lower | ci_upper | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| conversion_7d | primary | 0.0027981625820416856 | -0.0019330489641078983 | 0.007529374128191269 | 0.24637129953381165 | final |
| retention_7d | secondary | 0.0015776743139170601 | -0.009587936917723063 | 0.012743285545557183 | 0.7818180989491694 | final |
| revenue_30d | secondary | 0.09738864976283867 | 0.02154072682476675 | 0.17323657270091058 | 0.011852098056833293 | final |
| uninstall_rate | guardrail | 0.0015881717089286911 | -0.0014197121362353603 | 0.004596055554092742 | 0.3007152399508415 | final |
| support_ticket_rate | guardrail | 0.0012824804793409965 | -0.002268602158984862 | 0.0048335631176668545 | 0.4790242912042695 | final |
| exposure_rate | diagnostic | -0.0013476529140250548 | -0.005874597295468268 | 0.0031792914674181588 | 0.5595585289842053 | final |
| opportunity_rate | diagnostic | 0.0 | 0.0 | 0.0 | 1.0 | final |
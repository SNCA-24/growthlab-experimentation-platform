# Delayed Effect Scenario

## Summary
- scenario_id: `scenario_delayed_effect`
- scenario_type: `delayed_effect`
- input_dir: `/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_delayed_effect`
- trust_status: `pass`
- recommendation_proxy: `SHIP_GLOBAL`

## Trust Checks
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final, final, final, final, final, final, final`
- Evaluability: `underpowered, underpowered, underpowered, underpowered, underpowered, evaluable, evaluable`

## Validation Truth
- expected_srm_flag: `0`
- expected_recommendation: `SHIP_GLOBAL`
- expected_peeking_risk: `high_if_fixed_horizon_low_if_sequential_safe`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.003631353383035142`
- ci: `[-0.00099150789664482, 0.008254214662715104]`
- p_value: `0.12365315971221635`
- practical_threshold_met: `True`

## Metrics
| metric_name | metric_role | effect | ci_lower | ci_upper | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| conversion_7d | primary | 0.003631353383035142 | -0.00099150789664482 | 0.008254214662715104 | 0.12365315971221635 | final |
| retention_7d | secondary | 0.006647966257863208 | -0.004574510686657445 | 0.01787044320238386 | 0.24561052523257465 | final |
| revenue_30d | secondary | 0.035012224250015045 | -0.036719541684251455 | 0.10674399018428155 | 0.3387235487921507 | final |
| uninstall_rate | guardrail | 0.0002566854597417026 | -0.0026620033653078465 | 0.0031753742847912517 | 0.8631405375370214 | final |
| support_ticket_rate | guardrail | 0.0004135457679423152 | -0.003250476559754836 | 0.004077568095639467 | 0.8249176475357649 | final |
| exposure_rate | diagnostic | -0.0005704605856905465 | -0.005238039557830983 | 0.00409711838644989 | 0.8106767918427957 | final |
| opportunity_rate | diagnostic | 0.0 | 0.0 | 0.0 | 1.0 | final |
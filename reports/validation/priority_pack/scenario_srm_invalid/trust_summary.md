# Invalid SRM Scenario

## Summary
- scenario_id: `scenario_srm_invalid`
- scenario_type: `srm_invalid`
- input_dir: `/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_srm_invalid`
- trust_status: `fail`
- recommendation_proxy: `INVESTIGATE_INVALID_EXPERIMENT`

## Trust Checks
- SRM: `fail` (srm_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final, final, final, final, final, final, final`
- Evaluability: `underpowered, underpowered, underpowered, underpowered, underpowered, evaluable, evaluable`

## Validation Truth
- expected_srm_flag: `1`
- expected_recommendation: `INVESTIGATE_INVALID_EXPERIMENT`
- expected_peeking_risk: `low`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.005132824290447469`
- ci: `[0.00019794361285451444, 0.010067704968040424]`
- p_value: `0.0414929474073491`
- practical_threshold_met: `True`

## Metrics
| metric_name | metric_role | effect | ci_lower | ci_upper | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| conversion_7d | primary | 0.005132824290447469 | 0.00019794361285451444 | 0.010067704968040424 | 0.0414929474073491 | final |
| retention_7d | secondary | 0.005913290932024945 | -0.005849112213228931 | 0.01767569407727882 | 0.3244415630119486 | final |
| revenue_30d | secondary | 0.08459096955045609 | 0.011676690156940103 | 0.15750524894397205 | 0.022978529815493642 | final |
| uninstall_rate | guardrail | -0.0017953512837528864 | -0.004949579636532923 | 0.0013588770690271504 | 0.2645802850925074 | final |
| support_ticket_rate | guardrail | -0.00042844248621677974 | -0.004086016014549731 | 0.0032291310421161718 | 0.8184025864535718 | final |
| exposure_rate | diagnostic | 0.0016545842430633062 | -0.0030832697720415206 | 0.006392438258168133 | 0.49365620257786347 | final |
| opportunity_rate | diagnostic | 0.0 | 0.0 | 0.0 | 1.0 | final |
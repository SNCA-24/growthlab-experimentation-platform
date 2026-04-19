# A/A Null Test

## Summary
- scenario_id: `scenario_aa_null`
- scenario_type: `aa_null`
- input_dir: `/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_aa_null`
- trust_status: `pass`
- recommendation_proxy: `HOLD_INCONCLUSIVE`

## Trust Checks
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final, final, final, final, final, final, final`
- Evaluability: `underpowered, underpowered, underpowered, underpowered, underpowered, evaluable, evaluable`

## Validation Truth
- expected_srm_flag: `0`
- expected_recommendation: `HOLD_INCONCLUSIVE`
- expected_peeking_risk: `low`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.0008015930463208462`
- ci: `[-0.0036631193958983023, 0.005266305488539995]`
- p_value: `0.7249080187839607`
- practical_threshold_met: `False`

## Metrics
| metric_name | metric_role | effect | ci_lower | ci_upper | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| conversion_7d | primary | 0.0008015930463208462 | -0.0036631193958983023 | 0.005266305488539995 | 0.7249080187839607 | final |
| retention_7d | secondary | -0.0031862028566051748 | -0.014417870414467782 | 0.008045464701257433 | 0.5781925968709389 | final |
| revenue_30d | secondary | -0.025956492311428603 | -0.09502341850705875 | 0.04311043388420155 | 0.46135591822742583 | final |
| uninstall_rate | guardrail | 0.00120359274892428 | -0.0016782331374861274 | 0.004085418635334688 | 0.4130095786002581 | final |
| support_ticket_rate | guardrail | 0.0011462350724235973 | -0.0026157133446164343 | 0.004908183489463629 | 0.5503671568732131 | final |
| exposure_rate | diagnostic | -0.0016710968468525156 | -0.006249973874820088 | 0.0029077801811150565 | 0.47440349121001235 | final |
| opportunity_rate | diagnostic | 0.0 | 0.0 | 0.0 | 1.0 | final |
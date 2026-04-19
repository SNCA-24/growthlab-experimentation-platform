# Pre-Registered Segment-Only Win

## Summary
- scenario_id: `scenario_segment_only_win`
- scenario_type: `segment_only_win`
- input_dir: `/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_segment_only_win`
- trust_status: `pass`
- recommendation_proxy: `SHIP_TARGETED_SEGMENTS`

## Trust Checks
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final, final, final, final, final, final, final`
- Evaluability: `underpowered, underpowered, evaluable, underpowered, underpowered, evaluable, evaluable`

## Validation Truth
- expected_srm_flag: `0`
- expected_recommendation: `SHIP_TARGETED_SEGMENTS`
- expected_peeking_risk: `low`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.004570169882662151`
- ci: `[0.0008400667816957155, 0.008300272983628586]`
- p_value: `0.016335451768701992`
- practical_threshold_met: `True`

## Metrics
| metric_name | metric_role | effect | ci_lower | ci_upper | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| conversion_7d | primary | 0.004570169882662151 | 0.0008400667816957155 | 0.008300272983628586 | 0.016335451768701992 | final |
| retention_7d | secondary | 0.005344062365227442 | -0.004253550748704871 | 0.014941675479159755 | 0.2751165558158095 | final |
| revenue_30d | secondary | 0.036464129326123196 | -0.021062149843843143 | 0.09399040849608953 | 0.21409459005878273 | final |
| uninstall_rate | guardrail | -0.001666338924616581 | -0.0042976911562882915 | 0.0009650133070551294 | 0.21453268560306693 | final |
| support_ticket_rate | guardrail | 0.00171017931187643 | -0.0013059324687446005 | 0.004726291092497461 | 0.26641649938511924 | final |
| exposure_rate | diagnostic | 0.00206192454700449 | -0.0018484155420658982 | 0.005972264636074878 | 0.30136314907873585 | final |
| opportunity_rate | diagnostic | 0.0 | 0.0 | 0.0 | 1.0 | final |
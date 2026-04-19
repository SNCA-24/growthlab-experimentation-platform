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
- Evaluability: `underpowered, evaluable, evaluable, underpowered, underpowered, evaluable, evaluable`

## Validation Truth
- expected_srm_flag: `0`
- expected_recommendation: `SHIP_TARGETED_SEGMENTS`
- expected_peeking_risk: `low`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.0012600133175621094`
- ci: `[-0.0011584808017236887, 0.0036785074368479074]`
- p_value: `0.3071915493251627`
- practical_threshold_met: `False`

## Metrics
| metric_name | metric_role | effect | ci_lower | ci_upper | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| conversion_7d | primary | 0.0012600133175621094 | -0.0011584808017236887 | 0.0036785074368479074 | 0.3071915493251627 | final |
| retention_7d | secondary | 0.006008971282776082 | 7.199765403956108e-05 | 0.011945944911512603 | 0.04728574144970521 | final |
| revenue_30d | secondary | 0.04112934363189824 | 0.004708173665728621 | 0.07755051359806786 | 0.026875502901047454 | final |
| uninstall_rate | guardrail | 0.0007886783173210853 | -0.0007478107343228822 | 0.002325167368965053 | 0.3143881562097677 | final |
| support_ticket_rate | guardrail | -0.0014591485701972613 | -0.003310069497545881 | 0.00039177235715135827 | 0.122317573873155 | final |
| exposure_rate | diagnostic | -0.0006833872358593673 | -0.003141059994875526 | 0.0017742855231567913 | 0.5857539687573206 | final |
| opportunity_rate | diagnostic | 0.0 | 0.0 | 0.0 | 1.0 | final |
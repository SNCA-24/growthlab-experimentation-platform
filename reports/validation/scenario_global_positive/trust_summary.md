# Global Positive Effect

## Summary
- scenario_id: `scenario_global_positive`
- scenario_type: `global_positive`
- input_dir: `/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_global_positive`
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
- expected_peeking_risk: `low`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `0.0035984028781426564`
- ci: `[-0.001000279977099886, 0.0081970857333852]`
- p_value: `0.1251107225185586`
- practical_threshold_met: `True`

## Metrics
| metric_name | metric_role | effect | ci_lower | ci_upper | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| conversion_7d | primary | 0.0035984028781426564 | -0.001000279977099886 | 0.0081970857333852 | 0.1251107225185586 | final |
| retention_7d | secondary | 0.017089830751540802 | 0.00581668754256629 | 0.028362973960515313 | 0.0029674867253282056 | final |
| revenue_30d | secondary | 0.12787498862616453 | 0.05735254379775867 | 0.1983974334545704 | 0.00038008374667852785 | final |
| uninstall_rate | guardrail | -0.0026554292353548857 | -0.005662214780896524 | 0.00035135631018675274 | 0.08346050559679274 | final |
| support_ticket_rate | guardrail | 0.0013149140704902772 | -0.002343108120287 | 0.004972936261267554 | 0.48108578795314383 | final |
| exposure_rate | diagnostic | 0.001449118549490258 | -0.0033144408849260787 | 0.006212677983906595 | 0.5509991021360867 | final |
| opportunity_rate | diagnostic | 0.0 | 0.0 | 0.0 | 1.0 | final |
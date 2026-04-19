# Low Power / Noisy Experiment

## Summary
- scenario_id: `scenario_low_power_noisy`
- scenario_type: `low_power_noisy`
- input_dir: `/Users/chaitu/Downloads/growthlab/data/synthetic/scenario_low_power_noisy`
- trust_status: `pass`
- recommendation_proxy: `RERUN_UNDERPOWERED`

## Trust Checks
- SRM: `pass` (srm_not_detected)
- Missingness: `pass` (missingness_within_threshold)
- Exposure sanity: `pass` (exposure_opportunity_sane)
- Maturity: `final, final, final, final, final, final, final`
- Evaluability: `insufficient_sample, insufficient_sample, insufficient_sample, insufficient_sample, insufficient_sample, insufficient_sample, insufficient_sample`

## Validation Truth
- expected_srm_flag: `0`
- expected_recommendation: `RERUN_UNDERPOWERED`
- expected_peeking_risk: `medium`

## Primary Metric
- metric_name: `conversion_7d`
- effect: `-0.0004526149490141351`
- ci: `[-0.011063554545086767, 0.010158324647058497]`
- p_value: `0.9333513958485369`
- practical_threshold_met: `False`

## Metrics
| metric_name | metric_role | effect | ci_lower | ci_upper | p_value | status |
| --- | --- | --- | --- | --- | --- | --- |
| conversion_7d | primary | -0.0004526149490141351 | -0.011063554545086767 | 0.010158324647058497 | 0.9333513958485369 | final |
| retention_7d | secondary | 0.019346724389092906 | -0.010183308780759053 | 0.04887675755894487 | 0.19903553932157703 | final |
| revenue_30d | secondary | 0.05753366732188159 | -0.11306156700983733 | 0.2281289016536005 | 0.5084947212942699 | final |
| uninstall_rate | guardrail | 0.0038712324832269832 | -0.004092391611616385 | 0.011834856578070352 | 0.34059365559629207 | final |
| support_ticket_rate | guardrail | -0.0027161000430866444 | -0.011801194190138987 | 0.006368994103965698 | 0.5577935146887394 | final |
| exposure_rate | diagnostic | 0.005851576766039535 | -0.008397251615311142 | 0.020100405147390213 | 0.42075714285804744 | final |
| opportunity_rate | diagnostic | 0.0 | 0.0 | 0.0 | 1.0 | final |
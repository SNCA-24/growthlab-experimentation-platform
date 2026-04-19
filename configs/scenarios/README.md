# GrowthLab Simulator Scenario Pack v0.1

This starter pack includes the first two scenarios to implement:

1. `scenario_aa_null.yaml`
   - used for false-positive control, SRM sanity, and trust-layer validation
2. `scenario_global_positive.yaml`
   - used to verify positive effect recovery, CUPED gain, and global ship behavior

## Why these first
They are the highest-value scenarios because they establish:
- whether the stats engine is trustworthy
- whether the decision engine behaves sensibly on a clean win
- whether the synthetic pipeline can populate the canonical schema end-to-end

## Next suggested scenarios
- `scenario_guardrail_harm.yaml`
- `scenario_segment_only_win.yaml`
- `scenario_srm_invalid.yaml`
- `scenario_low_power_noisy.yaml`
- `scenario_delayed_effect.yaml`


# GrowthLab Simulator Scenario Pack v0.2

This pack adds the next three policy-stressing scenarios:

1. `scenario_guardrail_harm.yaml`
   - primary metric wins, but guardrails fail
2. `scenario_segment_only_win.yaml`
   - global result is weak, but a pre-registered segment can ship
3. `scenario_srm_invalid.yaml`
   - trust layer must stop the decision before any ship logic

## Combined progression
Together with v0.1, you now have the five highest-value starter scenarios:
- A/A null
- global positive
- guardrail harm
- segment-only win
- SRM invalid

## Next suggested scenarios
- `scenario_low_power_noisy.yaml`
- `scenario_delayed_effect.yaml`


This pack adds the final two core starter scenarios:

1. `scenario_low_power_noisy.yaml`
   - validates rerun / underpowered behavior
2. `scenario_delayed_effect.yaml`
   - validates interim vs final reads and delayed treatment realization

## Starter library now complete
Across v0.1 + v0.2 + v0.3, the core starter scenario library now covers:
- A/A null
- global positive
- guardrail harm
- segment-only win
- SRM invalid
- low power / noisy
- delayed effect

This is enough to begin implementation of:
- simulator
- validation harness
- trust checks
- core analysis engine
- decision engine
- UI demo flows
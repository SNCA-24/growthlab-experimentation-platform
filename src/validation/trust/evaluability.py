from __future__ import annotations

import pandas as pd

from core.contracts.policy_contracts import PolicyContract

from ._models import EvaluabilityResult, EvaluabilityState, TrustState


def evaluate_metric_evaluability(
    summary_frame: pd.DataFrame,
    *,
    policy: PolicyContract,
) -> list[EvaluabilityResult]:
    trust = policy.trust_checks
    results: list[EvaluabilityResult] = []
    for row in summary_frame.to_dict(orient="records"):
        metric_name = str(row["metric_name"])
        total_n = int(row.get("analyzed_n", 0) or 0)
        control_n = int(row.get("control_n", 0) or 0)
        treatment_n = int(row.get("treatment_n", 0) or 0)
        practical_threshold_value = row.get("practical_threshold_value")
        practical_threshold_type = row.get("practical_threshold_type")
        mde_at_target_power = row.get("mde_at_target_power")
        evaluable_flag = bool(row.get("practical_threshold_evaluable", False))

        if trust.min_total_sample_size and total_n < trust.min_total_sample_size:
            status = EvaluabilityState.insufficient_sample
            state = TrustState.warn
            message = "below_min_total_sample_size"
        elif trust.min_group_sample_size and min(control_n, treatment_n) < trust.min_group_sample_size:
            status = EvaluabilityState.insufficient_sample
            state = TrustState.warn
            message = "below_min_group_sample_size"
        elif evaluable_flag:
            status = EvaluabilityState.evaluable
            state = TrustState.pass_
            message = "practical_threshold_evaluable"
        else:
            status = EvaluabilityState.underpowered
            state = TrustState.warn
            message = "practical_threshold_underpowered"

        results.append(
            EvaluabilityResult(
                metric_name=metric_name,
                state=state,
                status=status,
                total_n=total_n,
                control_n=control_n,
                treatment_n=treatment_n,
                practical_threshold_value=float(practical_threshold_value) if practical_threshold_value is not None else None,
                practical_threshold_type=str(practical_threshold_type) if practical_threshold_type is not None else None,
                mde_at_target_power=float(mde_at_target_power) if mde_at_target_power is not None else None,
                evaluable=evaluable_flag,
                message=message,
            )
        )
    return results

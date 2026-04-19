from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from core.contracts.policy_contracts import PolicyContract

from ._models import MissingnessCheckResult, TrustState


def evaluate_missingness(
    frame: pd.DataFrame,
    *,
    relevant_columns: Iterable[str] | None,
    policy: PolicyContract,
) -> MissingnessCheckResult:
    trust = policy.trust_checks
    if not trust.enabled:
        return MissingnessCheckResult(
            state=TrustState.pass_,
            max_missingness_rate=trust.max_missingness_rate,
            overall_missingness_rate=0.0,
            column_missingness_rates={},
            message="trust_checks_disabled",
        )

    columns = list(relevant_columns or frame.columns)
    if not columns:
        return MissingnessCheckResult(
            state=TrustState.pass_,
            max_missingness_rate=trust.max_missingness_rate,
            overall_missingness_rate=0.0,
            column_missingness_rates={},
            message="no_relevant_columns",
        )

    column_missingness_rates = {
        column: float(frame[column].isna().mean()) if column in frame.columns else 1.0
        for column in columns
    }
    overall_missingness_rate = float(sum(column_missingness_rates.values()) / len(column_missingness_rates))
    problematic_columns = [column for column, rate in column_missingness_rates.items() if rate > trust.max_missingness_rate]

    if problematic_columns or overall_missingness_rate > trust.max_missingness_rate:
        state = TrustState.fail
        message = "missingness_above_threshold"
    elif any(rate > (trust.max_missingness_rate / 2.0) for rate in column_missingness_rates.values()):
        state = TrustState.warn
        message = "missingness_near_threshold"
    else:
        state = TrustState.pass_
        message = "missingness_within_threshold"

    return MissingnessCheckResult(
        state=state,
        max_missingness_rate=trust.max_missingness_rate,
        overall_missingness_rate=overall_missingness_rate,
        column_missingness_rates=column_missingness_rates,
        problematic_columns=problematic_columns,
        message=message,
    )

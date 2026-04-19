from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from core.contracts.experiment_contracts import ExperimentContract
from core.contracts.policy_contracts import PolicyContract

from ._models import SrmCheckResult, TrustState


def _observed_label_map(experiment: ExperimentContract) -> list[tuple[str, float]]:
    labels: list[tuple[str, float]] = []
    for variant in experiment.variants:
        label = "control" if variant.is_control else "treatment"
        labels.append((label, float(variant.weight)))
    return labels


def evaluate_srm(
    assignments: pd.DataFrame,
    experiment: ExperimentContract,
    policy: PolicyContract,
) -> SrmCheckResult:
    trust = policy.trust_checks
    if not trust.enabled or not trust.srm_check.enabled:
        return SrmCheckResult(
            state=TrustState.pass_,
            enabled=False,
            p_value=None,
            chi_square=None,
            degrees_of_freedom=None,
            observed_counts={},
            expected_counts={},
            observed_shares={},
            threshold_p_value=trust.srm_check.threshold_p_value if trust.srm_check else None,
            message="srm_check_disabled",
        )

    if "assigned_group" not in assignments.columns:
        raise ValueError("fact_assignments must include assigned_group for SRM evaluation")

    observed_counts_series = assignments["assigned_group"].astype(str).value_counts().reindex(
        [label for label, _ in _observed_label_map(experiment)],
        fill_value=0,
    )
    total = int(observed_counts_series.sum())
    if total <= 0:
        return SrmCheckResult(
            state=TrustState.fail,
            enabled=True,
            p_value=None,
            chi_square=None,
            degrees_of_freedom=None,
            observed_counts={},
            expected_counts={},
            observed_shares={},
            threshold_p_value=trust.srm_check.threshold_p_value,
            message="no_assignment_rows_available",
        )

    expected_shares = {label: share for label, share in _observed_label_map(experiment)}
    expected_counts = {label: total * share for label, share in expected_shares.items()}
    observed_counts = {label: int(value) for label, value in observed_counts_series.items()}
    observed_shares = {label: (count / total) for label, count in observed_counts.items()}

    obs = np.asarray(list(observed_counts.values()), dtype=np.float64)
    exp = np.asarray(list(expected_counts.values()), dtype=np.float64)
    if np.any(exp <= 0):
        raise ValueError("expected assignment shares must be strictly positive")

    chi_square, p_value = stats.chisquare(obs, f_exp=exp)
    threshold = trust.srm_check.threshold_p_value
    state = TrustState.fail if p_value < threshold else TrustState.pass_
    message = "srm_detected" if state == TrustState.fail else "srm_not_detected"
    return SrmCheckResult(
        state=state,
        enabled=True,
        p_value=float(p_value),
        chi_square=float(chi_square),
        degrees_of_freedom=max(len(obs) - 1, 1),
        observed_counts=observed_counts,
        expected_counts=expected_counts,
        observed_shares=observed_shares,
        threshold_p_value=threshold,
        message=message,
    )


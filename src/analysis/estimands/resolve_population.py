from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.contracts._common import PrimaryEstimand
from core.contracts.experiment_contracts import ExperimentContract


@dataclass(slots=True)
class ResolvedPopulation:
    estimand: PrimaryEstimand
    denominator_label: str
    mask: pd.Series
    total_n: int
    eligible_n: int
    selected_n: int


def resolve_population(experiment: ExperimentContract, outcomes: pd.DataFrame) -> ResolvedPopulation:
    if "assigned_group" not in outcomes.columns:
        raise ValueError("fact_user_outcomes must include assigned_group")

    total_n = len(outcomes)
    eligible_n = total_n

    if experiment.primary_estimand == PrimaryEstimand.itt_assigned:
        mask = pd.Series(True, index=outcomes.index)
        denominator_label = "assigned"
    elif experiment.primary_estimand == PrimaryEstimand.itt_opportunity:
        if "had_opportunity" not in outcomes.columns:
            raise ValueError("itt_opportunity requires had_opportunity in fact_user_outcomes")
        mask = outcomes["had_opportunity"].astype(int).eq(1)
        denominator_label = "opportunity"
    elif experiment.primary_estimand == PrimaryEstimand.tot_exposed:
        if "is_exposed" not in outcomes.columns:
            raise ValueError("tot_exposed requires is_exposed in fact_user_outcomes")
        mask = outcomes["is_exposed"].astype(int).eq(1)
        denominator_label = "exposed"
    else:
        raise ValueError(f"unsupported primary_estimand: {experiment.primary_estimand}")

    selected_n = int(mask.sum())
    if selected_n == 0:
        raise ValueError(f"no rows available for estimand {experiment.primary_estimand.value}")

    return ResolvedPopulation(
        estimand=experiment.primary_estimand,
        denominator_label=denominator_label,
        mask=mask,
        total_n=total_n,
        eligible_n=eligible_n,
        selected_n=selected_n,
    )


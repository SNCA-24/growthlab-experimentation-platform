from __future__ import annotations

import numpy as np
import pandas as pd

from core.contracts import ScenarioContract

from ._shared import utc_timestamp_range


def generate_fact_assignments(
    scenario: ScenarioContract,
    dim_users: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    experiment = scenario.experiment
    n_users = len(dim_users)

    treatment_variants = [variant for variant in experiment.variants if not variant.is_control]
    if len(treatment_variants) != 1:
        raise NotImplementedError("synthetic DGP currently supports exactly one treatment arm")
    treatment_share = treatment_variants[0].weight
    if scenario.pathology_flags.inject_srm and scenario.pathology_flags.srm_target_shares is not None:
        treatment_share = float(scenario.pathology_flags.srm_target_shares.get("treatment", treatment_share))
        if "treatment_a" in scenario.pathology_flags.srm_target_shares:
            treatment_share = float(scenario.pathology_flags.srm_target_shares["treatment_a"])
    treatment_share = float(np.clip(treatment_share, 0.0, 1.0))

    assigned_group = np.where(rng.random(n_users) < treatment_share, "treatment", "control")

    assignment_start = experiment.assignment_start_ts_utc
    assignment_end = experiment.assignment_end_ts_utc
    span_seconds = int((assignment_end - assignment_start).total_seconds())
    assignment_ts = utc_timestamp_range(assignment_start, n_users, span_seconds, rng)

    assignment_bucket = rng.integers(0, 10_000, size=n_users, endpoint=False, dtype=np.int32)

    return pd.DataFrame(
        {
            "experiment_id": experiment.experiment_id,
            "user_id": dim_users["user_id"].to_numpy(),
            "assignment_ts": assignment_ts,
            "assigned_group": assigned_group.astype(str),
            "assignment_bucket": assignment_bucket,
            "is_eligible": np.ones(n_users, dtype=np.int8),
            "assignment_reason": pd.Series(
                ["srm_injected" if scenario.pathology_flags.inject_srm else None] * n_users,
                dtype="object",
            ),
        }
    )

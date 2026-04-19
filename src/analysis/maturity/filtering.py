from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.contracts.metric_contracts import MetricContract


@dataclass(slots=True)
class MaturityFilterResult:
    filtered: pd.DataFrame
    total_n: int
    mature_n: int
    immature_n: int
    status: str


def filter_by_maturity(frame: pd.DataFrame, metric: MetricContract) -> MaturityFilterResult:
    total_n = len(frame)
    maturity_window_days = metric.maturity_window_days
    if maturity_window_days is None:
        return MaturityFilterResult(frame.copy(), total_n, total_n, 0, "final")

    if "analysis_window_days" in frame.columns:
        mature_mask = frame["analysis_window_days"].astype(int) >= maturity_window_days
    elif "days_since_first_opportunity" in frame.columns:
        mature_mask = frame["days_since_first_opportunity"].astype(int) >= maturity_window_days
    else:
        raise ValueError(
            f"metric '{metric.metric_name}' requires maturity filtering but no observation window column is present"
        )

    mature_n = int(mature_mask.sum())
    immature_n = total_n - mature_n
    filtered = frame.loc[mature_mask].copy()

    if mature_n == 0:
        status = "immature"
    elif immature_n > 0:
        status = "interim"
    else:
        status = "final"

    return MaturityFilterResult(filtered=filtered, total_n=total_n, mature_n=mature_n, immature_n=immature_n, status=status)

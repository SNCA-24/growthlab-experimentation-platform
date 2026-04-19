from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from ._models import MetricMaturityResult, TrustState


def evaluate_maturity(summary_frame: pd.DataFrame) -> list[MetricMaturityResult]:
    results: list[MetricMaturityResult] = []
    for row in summary_frame.to_dict(orient="records"):
        metric_name = str(row["metric_name"])
        maturity_window_days = row.get("maturity_window_days")
        total_n = int(row.get("total_n", 0) or 0)
        mature_n = int(row.get("mature_n", 0) or 0)
        immature_n = int(row.get("immature_n", 0) or 0)
        excluded_n = immature_n
        if maturity_window_days is None:
            state = TrustState.pass_
            maturity_status = "final"
            message = "maturity_not_required"
        elif mature_n <= 0:
            state = TrustState.fail
            maturity_status = "immature"
            message = "no_mature_rows"
        elif immature_n > 0:
            state = TrustState.warn
            maturity_status = "interim"
            message = "immature_rows_excluded"
        else:
            state = TrustState.pass_
            maturity_status = "final"
            message = "all_rows_mature"

        results.append(
            MetricMaturityResult(
                metric_name=metric_name,
                state=state,
                maturity_status=maturity_status,
                total_n=total_n,
                mature_n=mature_n,
                immature_n=immature_n,
                excluded_n=excluded_n,
                maturity_window_days=int(maturity_window_days) if maturity_window_days is not None else None,
                message=message,
            )
        )
    return results


from __future__ import annotations

import pandas as pd

from .._stats import cuped_adjust as _cuped_adjust


def adjust_for_covariate(y: pd.Series, x: pd.Series) -> tuple[pd.Series, float | None, str | None]:
    return _cuped_adjust(y, x)


def cuped_adjust(y: pd.Series, x: pd.Series) -> tuple[pd.Series, float | None, str | None]:
    return _cuped_adjust(y, x)


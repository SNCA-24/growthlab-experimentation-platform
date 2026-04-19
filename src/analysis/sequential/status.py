from __future__ import annotations


def classify_read_status(*, mature_n: int, immature_n: int) -> str:
    if mature_n <= 0:
        return "immature"
    if immature_n > 0:
        return "interim"
    return "final"


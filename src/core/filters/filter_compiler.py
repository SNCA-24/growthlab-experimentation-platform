from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..contracts import ComparisonOperator, FilterDefinition

ALLOWED_ANALYTICAL_COLUMNS = frozenset(
    {
        "user_id",
        "signup_date",
        "country",
        "platform",
        "acquisition_channel",
        "plan_tier",
        "tenure_days_at_experiment_start",
        "historical_sessions_28d",
        "historical_revenue_28d",
        "historical_conversion_flag",
        "historical_retention_score",
        "device_class",
        "region",
        "risk_score_baseline",
        "engagement_cluster",
    }
)


def _quote_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _compile_value(value: Any) -> str:
    if value is None:
        raise ValueError("null values are not supported in structured filters")
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, date) and not isinstance(value, datetime):
        return f"DATE {_quote_string(value.isoformat())}"
    if isinstance(value, datetime):
        return f"TIMESTAMPTZ {_quote_string(value.isoformat())}"
    return _quote_string(str(value))


def compile_filter(filter_definition: FilterDefinition) -> str:
    if filter_definition.column not in ALLOWED_ANALYTICAL_COLUMNS:
        raise ValueError(f"unknown filter column: {filter_definition.column}")

    operator_map = {
        ComparisonOperator.eq: "=",
        ComparisonOperator.ne: "<>",
        ComparisonOperator.in_: "IN",
        ComparisonOperator.not_in: "NOT IN",
        ComparisonOperator.ge: ">=",
        ComparisonOperator.gt: ">",
        ComparisonOperator.le: "<=",
        ComparisonOperator.lt: "<",
    }
    sql_operator = operator_map[filter_definition.op]

    if filter_definition.op in {ComparisonOperator.in_, ComparisonOperator.not_in}:
        assert filter_definition.values is not None
        values = ", ".join(_compile_value(value) for value in filter_definition.values)
        return f"{filter_definition.column} {sql_operator} ({values})"
    assert filter_definition.value is not None
    return f"{filter_definition.column} {sql_operator} {_compile_value(filter_definition.value)}"


def compile_filters(filters: list[FilterDefinition] | tuple[FilterDefinition, ...]) -> str:
    if not filters:
        return "TRUE"
    return " AND ".join(f"({compile_filter(filter_definition)})" for filter_definition in filters)


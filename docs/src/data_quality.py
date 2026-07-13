from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class QualityCheckResult:
    issue: str
    count: int
    details: str


def _count(condition: pd.Series) -> int:
    return int(condition.fillna(False).sum())


def data_quality_summary(df: pd.DataFrame, column_map: dict[str, str]) -> list[QualityCheckResult]:
    results: list[QualityCheckResult] = []

    results.append(QualityCheckResult("missing_values", int(df.isna().sum().sum()), "Total missing cells across all columns"))
    results.append(QualityCheckResult("duplicate_rows", int(df.duplicated().sum()), "Exact duplicate records"))

    qty = pd.to_numeric(df[column_map["order_quantity"]], errors="coerce") if column_map.get("order_quantity") else pd.Series(dtype="float64")
    unit_price = pd.to_numeric(df[column_map["unit_price"]], errors="coerce") if column_map.get("unit_price") else pd.Series(dtype="float64")
    unit_cost = pd.to_numeric(df[column_map["unit_cost"]], errors="coerce") if column_map.get("unit_cost") else pd.Series(dtype="float64")
    order_date = pd.to_datetime(df[column_map["order_date"]], errors="coerce") if column_map.get("order_date") else pd.Series(dtype="datetime64[ns]")

    if not qty.empty:
        results.append(QualityCheckResult("negative_or_zero_quantities", _count(qty <= 0), "Order quantity less than or equal to zero"))
    if not unit_price.empty:
        results.append(QualityCheckResult("negative_or_zero_unit_price", _count(unit_price <= 0), "Unit price less than or equal to zero"))
    if not unit_cost.empty:
        results.append(QualityCheckResult("negative_or_zero_unit_cost", _count(unit_cost <= 0), "Unit cost less than or equal to zero"))
    if not unit_price.empty and not unit_cost.empty:
        results.append(QualityCheckResult("unit_cost_greater_than_unit_price", _count(unit_cost > unit_price), "Potentially loss-making items"))
    if not order_date.empty:
        results.append(QualityCheckResult("date_parsing_problems", _count(order_date.isna()), "Unparseable order dates"))

    numeric_series = {"OrderQuantity": qty, "UnitPrice": unit_price, "UnitCost": unit_cost}
    for label, series in numeric_series.items():
        if series.empty:
            continue
        valid = series.dropna()
        if valid.empty:
            continue
        q1 = valid.quantile(0.25)
        q3 = valid.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = int(((series < lower) | (series > upper)).sum())
        results.append(QualityCheckResult(f"outliers_{label.lower()}", outliers, f"IQR outliers for {label}"))

    return results


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "missing_values": {column: int(count) for column, count in df.isna().sum().items()},
        "duplicate_rows": int(df.duplicated().sum()),
    }

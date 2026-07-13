from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator in (0, None) or pd.isna(denominator):
        return float('nan')
    return float(numerator) / float(denominator)


@dataclass
class KPISet:
    total_revenue: float
    total_profit: float
    profit_margin: float
    total_orders: int
    total_customers: int
    total_sales_teams: int
    average_order_value: float
    average_profit_per_order: float


def compute_kpis(df: pd.DataFrame) -> KPISet:
    revenue = float(df['Transaction Amount'].sum(skipna=True))
    profit = float(df['Profit'].sum(skipna=True))
    orders = int(len(df))
    customers = int(df['CustomerID'].nunique()) if 'CustomerID' in df.columns else 0
    teams = int(df['SalesTeamID'].nunique()) if 'SalesTeamID' in df.columns else 0
    aov = safe_divide(revenue, orders)
    avg_profit = safe_divide(profit, orders)
    margin = safe_divide(profit, revenue)
    return KPISet(revenue, profit, margin, orders, customers, teams, aov, avg_profit)


def aggregate_metric(df: pd.DataFrame, group_col: str, metric_col: str, sort_desc: bool = True) -> pd.DataFrame:
    result = df.groupby(group_col, dropna=False)[metric_col].sum().reset_index()
    result = result.sort_values(metric_col, ascending=not sort_desc)
    return result


def aggregate_margin(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    grouped = df.groupby(group_col, dropna=False).agg({'Transaction Amount': 'sum', 'Profit': 'sum'}).reset_index()
    grouped['Profit Margin'] = grouped.apply(lambda row: safe_divide(row['Profit'], row['Transaction Amount']), axis=1)
    return grouped.sort_values('Profit Margin', ascending=False)


def monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby('OrderMonth', dropna=False).agg({'Transaction Amount': 'sum', 'Profit': 'sum'}).reset_index()
    grouped = grouped.sort_values('OrderMonth')
    grouped['Revenue Growth'] = grouped['Transaction Amount'].pct_change()
    grouped['Profit Growth'] = grouped['Profit'].pct_change()
    return grouped


def quarterly_trends(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.assign(Quarter=df['OrderDate'].dt.to_period('Q').astype(str))
        .groupby('Quarter', dropna=False)
        .agg({'Transaction Amount': 'sum', 'Profit': 'sum'})
        .reset_index()
    )
    return grouped.sort_values('Quarter')


def top_bottom_customers(df: pd.DataFrame, top_n: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    if 'CustomerName' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    grouped = df.groupby('CustomerName').agg({'Transaction Amount': 'sum', 'Profit': 'sum'}).reset_index()
    top = grouped.sort_values('Transaction Amount', ascending=False).head(top_n)
    bottom = grouped.sort_values('Transaction Amount', ascending=True).head(top_n)
    return top, bottom


def concentration_metrics(df: pd.DataFrame, entity_col: str) -> pd.DataFrame:
    grouped = df.groupby(entity_col).agg({'Transaction Amount': 'sum'}).reset_index().sort_values('Transaction Amount', ascending=False)
    grouped['Revenue Contribution Percentage'] = grouped['Transaction Amount'] / grouped['Transaction Amount'].sum()
    grouped['Cumulative Contribution'] = grouped['Revenue Contribution Percentage'].cumsum()
    return grouped

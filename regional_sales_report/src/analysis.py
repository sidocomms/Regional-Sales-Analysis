from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .metrics import aggregate_margin, aggregate_metric, concentration_metrics, monthly_trends, quarterly_trends, top_bottom_customers


@dataclass
class AnalysisResults:
    region_revenue: pd.DataFrame
    region_profit: pd.DataFrame
    region_margin: pd.DataFrame
    channel_revenue: pd.DataFrame
    channel_profit: pd.DataFrame
    channel_margin: pd.DataFrame
    customer_revenue: pd.DataFrame
    customer_profit: pd.DataFrame
    team_revenue: pd.DataFrame
    team_profit: pd.DataFrame
    team_margin: pd.DataFrame
    monthly: pd.DataFrame
    quarterly: pd.DataFrame
    top_customers: pd.DataFrame
    bottom_customers: pd.DataFrame
    customer_concentration: pd.DataFrame
    product_revenue: pd.DataFrame | None
    product_profit: pd.DataFrame | None
    product_quantity: pd.DataFrame | None
    product_margin: pd.DataFrame | None


def build_analysis(df: pd.DataFrame, has_product: bool) -> AnalysisResults:
    region_col = 'Region' if 'Region' in df.columns else None
    channel_col = 'SalesChannel' if 'SalesChannel' in df.columns else None
    customer_col = 'CustomerName' if 'CustomerName' in df.columns else ('CustomerID' if 'CustomerID' in df.columns else None)
    team_col = 'SalesTeam' if 'SalesTeam' in df.columns else ('SalesTeamID' if 'SalesTeamID' in df.columns else None)
    product_col = 'Category' if 'Category' in df.columns else ('CategoryID' if 'CategoryID' in df.columns else None)

    region_revenue = aggregate_metric(df, region_col, 'Transaction Amount') if region_col else pd.DataFrame()
    region_profit = aggregate_metric(df, region_col, 'Profit') if region_col else pd.DataFrame()
    region_margin = aggregate_margin(df, region_col) if region_col else pd.DataFrame()

    channel_revenue = aggregate_metric(df, channel_col, 'Transaction Amount') if channel_col else pd.DataFrame()
    channel_profit = aggregate_metric(df, channel_col, 'Profit') if channel_col else pd.DataFrame()
    channel_margin = aggregate_margin(df, channel_col) if channel_col else pd.DataFrame()

    customer_revenue = aggregate_metric(df, customer_col, 'Transaction Amount') if customer_col else pd.DataFrame()
    customer_profit = aggregate_metric(df, customer_col, 'Profit') if customer_col else pd.DataFrame()
    team_revenue = aggregate_metric(df, team_col, 'Transaction Amount') if team_col else pd.DataFrame()
    team_profit = aggregate_metric(df, team_col, 'Profit') if team_col else pd.DataFrame()
    team_margin = aggregate_margin(df, team_col) if team_col else pd.DataFrame()

    monthly = monthly_trends(df)
    quarterly = quarterly_trends(df)
    top_customers, bottom_customers = top_bottom_customers(df)
    customer_concentration = concentration_metrics(df, customer_col) if customer_col else pd.DataFrame()

    product_revenue = aggregate_metric(df, product_col, 'Transaction Amount') if has_product and product_col else None
    product_profit = aggregate_metric(df, product_col, 'Profit') if has_product and product_col else None
    product_quantity = aggregate_metric(df, product_col, 'OrderQuantity') if has_product and product_col else None
    product_margin = aggregate_margin(df, product_col) if has_product and product_col else None

    return AnalysisResults(
        region_revenue=region_revenue,
        region_profit=region_profit,
        region_margin=region_margin,
        channel_revenue=channel_revenue,
        channel_profit=channel_profit,
        channel_margin=channel_margin,
        customer_revenue=customer_revenue,
        customer_profit=customer_profit,
        team_revenue=team_revenue,
        team_profit=team_profit,
        team_margin=team_margin,
        monthly=monthly,
        quarterly=quarterly,
        top_customers=top_customers,
        bottom_customers=bottom_customers,
        customer_concentration=customer_concentration,
        product_revenue=product_revenue,
        product_profit=product_profit,
        product_quantity=product_quantity,
        product_margin=product_margin,
    )

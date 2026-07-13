from __future__ import annotations

from typing import Any

import pandas as pd


def format_currency(value: float) -> str:
    return f'${value:,.0f}'


def summarize_kpis(kpis: dict[str, Any]) -> dict[str, str]:
    return {
        'headline': f"Revenue of {format_currency(kpis['total_revenue'])} and profit of {format_currency(kpis['total_profit'])} were generated across {kpis['total_orders']:,} orders.",
        'margin': f"Overall profit margin was {kpis['profit_margin']:.1%}.",
        'scale': f"The business served {kpis['total_customers']:,} customers and {kpis['total_sales_teams']:,} sales teams.",
    }


def top_line_insights(df: pd.DataFrame) -> list[str]:
    insights: list[str] = []
    if 'Profit Margin' in df.columns:
        low_margin = df['Profit Margin'].dropna().quantile(0.25)
        insights.append(f"Lower-quartile profit margin is about {low_margin:.1%}, so margin pressure is present in part of the portfolio.")
    if 'OrderMonth' in df.columns:
        insights.append('Monthly trends should be reviewed for seasonality and growth inflection points in the interactive chart.')
    return insights


def build_business_problems(region_margin: pd.DataFrame, channel_margin: pd.DataFrame, customer_concentration: pd.DataFrame) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    if not region_margin.empty:
        worst_region = region_margin.sort_values('Profit Margin').head(1).iloc[0]
        problems.append({
            'problem': 'Some regions are likely under-monetized relative to their sales volume.',
            'evidence': f"Lowest regional margin is {worst_region.get('Profit Margin', 0):.1%}.",
            'impact': 'Weak regional profitability can dilute enterprise margin and mask top-line growth.',
            'drivers': 'Possible mix, pricing, or sales execution differences across regions.',
            'strategy': 'Review pricing, discounting, and sales coverage in low-margin regions.',
            'kpi': 'Regional profit margin',
        })
    if not channel_margin.empty:
        worst_channel = channel_margin.sort_values('Profit Margin').head(1).iloc[0]
        problems.append({
            'problem': 'Channel profitability is uneven and may require channel-specific policies.',
            'evidence': f"Lowest channel margin is {worst_channel.get('Profit Margin', 0):.1%}.",
            'impact': 'High-volume low-margin channels can expand revenue without improving profit.',
            'drivers': 'Channel mix, order size, or discount differences.',
            'strategy': 'Tune offers and minimum margin thresholds by channel.',
            'kpi': 'Channel profit margin',
        })
    if not customer_concentration.empty and not customer_concentration.empty:
        top_share = float(customer_concentration.head(5)['Revenue Contribution Percentage'].sum())
        problems.append({
            'problem': 'Revenue concentration may be elevated in a small group of customers.',
            'evidence': f"Top 5 customers contribute {top_share:.1%} of revenue.",
            'impact': 'Dependence on a narrow customer base raises retention risk.',
            'drivers': 'Account concentration or uneven customer coverage.',
            'strategy': 'Build retention plans and whitespace expansion for key accounts.',
            'kpi': 'Top-customer revenue share',
        })
    return problems

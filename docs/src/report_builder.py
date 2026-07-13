from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .analysis import AnalysisResults
from .insights import build_business_problems, summarize_kpis, top_line_insights
from .metrics import KPISet
from .theme import CORPORATE_THEME
from .visuals import (
    bar_chart,
    box_plot,
    channel_orders_bar_chart,
    channel_orders_revenue_scatter,
    combo_chart,
    donut_chart,
    executive_monthly_performance_chart,
    growth_trend_chart,
    heatmap,
    kpi_cards,
    line_chart,
    ranked_table_html,
    regional_revenue_map,
    sales_team_scatter,
    sales_team_performance_chart,
    scatter_plot,
)


def _df_to_records(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    return df.head(limit).fillna('').to_dict(orient='records')


def _build_logo_data_uri(project_dir: Path) -> str:
    logo_path = project_dir.parent / 'Sidocomms Logo.jpg'
    if not logo_path.exists():
        return ''
    encoded = base64.b64encode(logo_path.read_bytes()).decode('ascii')
    return f'data:image/jpeg;base64,{encoded}'


def _build_storyline_notes(
    region_revenue: pd.DataFrame,
    team_summary: pd.DataFrame,
    channel_summary: pd.DataFrame,
    has_geographic_map: bool,
) -> list[str]:
    notes: list[str] = []
    if not region_revenue.empty:
        top_region = region_revenue.sort_values('Transaction Amount', ascending=False).iloc[0]
        bottom_region = region_revenue.sort_values('Transaction Amount', ascending=True).iloc[0]
        notes.append(
            f"Highest-revenue region is {top_region[region_revenue.columns[0]]} at ${top_region['Transaction Amount']:,.0f}, "
            f"while the lowest is {bottom_region[region_revenue.columns[0]]} at ${bottom_region['Transaction Amount']:,.0f}."
        )
    if has_geographic_map:
        notes.append('State-level revenue shading shows where performance is geographically concentrated and where coverage is lighter.')
    if not team_summary.empty:
        strongest_team = team_summary.sort_values('Revenue', ascending=False).iloc[0]
        weakest_team = team_summary.sort_values('Revenue', ascending=True).iloc[0]
        notes.append(
            f"Strongest sales team by revenue is {strongest_team['SalesTeam']} (${strongest_team['Revenue']:,.0f}); "
            f"weakest is {weakest_team['SalesTeam']} (${weakest_team['Revenue']:,.0f})."
        )
    if not channel_summary.empty:
        volume_leader = channel_summary.sort_values('Orders', ascending=False).iloc[0]
        weak_margin = channel_summary.sort_values('Profit Margin', ascending=True).iloc[0]
        notes.append(
            f"{volume_leader['SalesChannel']} carries the highest order volume ({volume_leader['Orders']:,.0f}), "
            f"while {weak_margin['SalesChannel']} has the weakest margin ({weak_margin['Profit Margin']:.1%})."
        )
    return notes


def _resolve_order_id_column(df: pd.DataFrame) -> str | None:
    candidates = ['OrderID', 'OrderId', 'OrderNumber', 'OrderNumberID', 'Order ID', 'Order Number', 'Order Number ID']
    by_normalized = {column.lower().replace(' ', '').replace('_', ''): column for column in df.columns}
    for candidate in candidates:
        normalized = candidate.lower().replace(' ', '').replace('_', '')
        if normalized in by_normalized:
            return by_normalized[normalized]
    return None


def _prepare_monthly_performance_df(filtered_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if filtered_df.empty or 'OrderMonth' not in filtered_df.columns:
        return pd.DataFrame(), 'Benchmark'

    monthly = (
        filtered_df.groupby('OrderMonth', dropna=False)
        .agg({'Transaction Amount': 'sum', 'Profit': 'sum'})
        .rename(columns={'Transaction Amount': 'Revenue'})
        .reset_index()
        .sort_values('OrderMonth')
    )
    monthly_orders = filtered_df.groupby('OrderMonth', dropna=False).size().rename('Orders').reset_index()
    monthly = monthly.merge(monthly_orders, on='OrderMonth', how='left')
    monthly['Profit Margin'] = monthly['Profit'] / monthly['Revenue']
    monthly['Average Order Value'] = monthly['Revenue'] / monthly['Orders']
    monthly['Profit Diff Prev'] = monthly['Profit'].diff().fillna(0)

    benchmark_label = ''
    benchmark_series = pd.Series(dtype='float64')

    target_columns = [column for column in ['Monthly Revenue Target', 'Revenue Target', 'MonthlyRevenueTarget'] if column in filtered_df.columns]
    if target_columns:
        target_col = target_columns[0]
        monthly_target = (
            filtered_df.groupby('OrderMonth', dropna=False)[target_col]
            .mean()
            .reset_index()
            .rename(columns={target_col: 'Benchmark'})
            .sort_values('OrderMonth')
        )
        monthly = monthly.merge(monthly_target, on='OrderMonth', how='left')
        if monthly['Benchmark'].notna().any():
            benchmark_series = monthly['Benchmark']
            benchmark_label = f'Monthly Revenue Target ({target_col})'

    if benchmark_series.empty:
        if monthly['Revenue'].notna().any():
            benchmark_series = pd.Series(monthly['Revenue'].mean(), index=monthly.index)
            benchmark_label = 'Average Monthly Revenue'
        elif len(monthly) >= 12:
            benchmark_series = monthly['Revenue'].rolling(window=12, min_periods=1).mean()
            benchmark_label = 'Rolling 12-Month Average Revenue'
        else:
            benchmark_series = pd.Series(monthly['Revenue'].mean(skipna=True), index=monthly.index)
            benchmark_label = 'Overall Mean Monthly Revenue'

    monthly['Benchmark'] = benchmark_series
    monthly['Revenue Diff Benchmark'] = monthly['Revenue'] - monthly['Benchmark']
    return monthly, benchmark_label


def _monthly_performance_insight(monthly_df: pd.DataFrame, benchmark_label: str) -> str:
    if monthly_df.empty:
        return ''
    above_share = (monthly_df['Revenue'] > monthly_df['Benchmark']).mean()
    last_3 = monthly_df.tail(3)
    margin_recent = last_3['Profit Margin'].mean()
    margin_all = monthly_df['Profit Margin'].mean()
    margin_direction = 'declined' if margin_recent < margin_all else 'improved'
    best_revenue_month = monthly_df.loc[monthly_df['Revenue'].idxmax(), 'OrderMonth']
    best_label = pd.to_datetime(best_revenue_month).strftime('%b %Y') if pd.notna(best_revenue_month) else 'N/A'
    return (
        f"Revenue stayed above the {benchmark_label.lower()} in {above_share:.0%} of months. "
        f"Peak revenue occurred in {best_label}, while recent profit margin {margin_direction} versus the full-period average."
    )


def build_report(
    project_dir: Path,
    output_path: Path,
    kpis: KPISet,
    analysis: AnalysisResults,
    quality_results: list[Any],
    workbook_info: dict[str, Any],
    profile: dict[str, Any],
    filtered_df: pd.DataFrame,
    has_product: bool,
) -> Path:
    env = Environment(
        loader=FileSystemLoader(str(project_dir / 'templates')),
        autoescape=select_autoescape(['html', 'xml']),
    )
    template = env.get_template('report_template.html')

    kpi_dict = kpis.__dict__
    summary = summarize_kpis(kpi_dict)
    business_problems = build_business_problems(analysis.region_margin, analysis.channel_margin, analysis.customer_concentration)
    top_insights = top_line_insights(filtered_df)

    order_id_col = _resolve_order_id_column(filtered_df)

    filter_columns = [
        column
        for column in [
            'OrderDate',
            'OrderMonth',
            'Region',
            'SalesChannel',
            'CustomerName',
            'SalesTeam',
            'Category',
            'State',
            'StateCode',
            'OrderQuantity',
            'UnitPrice',
            'UnitCost',
            'Total Cost',
            'Transaction Amount',
            'Profit',
            'Profit Margin',
        ]
        if column in filtered_df.columns
    ]
    if order_id_col and order_id_col not in filter_columns:
        filter_columns.append(order_id_col)
    filter_records = filtered_df[filter_columns].copy()
    if 'OrderDate' in filter_records.columns:
        filter_records['OrderDate'] = pd.to_datetime(filter_records['OrderDate'], errors='coerce').dt.strftime('%Y-%m-%d')
    if 'OrderMonth' in filter_records.columns:
        order_month_series = pd.to_datetime(filter_records['OrderMonth'], errors='coerce')
        filter_records['OrderMonth'] = order_month_series.dt.strftime('%Y-%m-%d')
        filter_records['Year'] = order_month_series.dt.year
        filter_records['Quarter'] = 'Q' + order_month_series.dt.quarter.astype('Int64').astype(str)
        filter_records['MonthNumber'] = order_month_series.dt.month
        filter_records['MonthName'] = order_month_series.dt.strftime('%b')
    if order_id_col and order_id_col in filter_records.columns:
        filter_records['OrderIdentifier'] = filter_records[order_id_col].astype(str)
    filter_records = filter_records.fillna('')
    filter_options = {
        'regions': sorted([value for value in filtered_df['Region'].dropna().unique().tolist()]) if 'Region' in filtered_df.columns else [],
        'channels': sorted([value for value in filtered_df['SalesChannel'].dropna().unique().tolist()]) if 'SalesChannel' in filtered_df.columns else [],
        'customers': sorted([value for value in filtered_df['CustomerName'].dropna().unique().tolist()]) if 'CustomerName' in filtered_df.columns else [],
        'teams': sorted([value for value in filtered_df['SalesTeam'].dropna().unique().tolist()]) if 'SalesTeam' in filtered_df.columns else [],
        'dates': sorted([value.strftime('%Y-%m-%d') for value in pd.to_datetime(filtered_df['OrderDate'], errors='coerce').dropna().dt.to_pydatetime().tolist()]) if 'OrderDate' in filtered_df.columns else [],
    }

    team_summary = (
        filtered_df.groupby('SalesTeam', dropna=False)
        .agg({'Transaction Amount': 'sum', 'Profit': 'sum', 'OrderQuantity': 'sum'})
        .rename(columns={'Transaction Amount': 'Revenue'})
        .reset_index()
        if 'SalesTeam' in filtered_df.columns
        else pd.DataFrame()
    )
    if not team_summary.empty:
        order_counts = filtered_df.groupby('SalesTeam', dropna=False).size().rename('Orders').reset_index()
        team_summary = team_summary.merge(order_counts, on='SalesTeam', how='left')
        team_summary['Profit Margin'] = team_summary['Profit'] / team_summary['Revenue']
        team_summary['Profit For Sizing'] = team_summary['Profit'].clip(lower=0) + 1
        team_summary = team_summary.sort_values('Revenue', ascending=False)
        team_summary['SalesTeamFilter'] = team_summary['SalesTeam']
        top_n = 10
        if len(team_summary) > top_n:
            other = pd.DataFrame(
                [
                    {
                        'SalesTeam': f'Other ({len(team_summary) - top_n} teams)',
                        'Revenue': team_summary.iloc[top_n:]['Revenue'].sum(),
                        'Profit': team_summary.iloc[top_n:]['Profit'].sum(),
                        'OrderQuantity': team_summary.iloc[top_n:]['OrderQuantity'].sum(),
                        'Orders': team_summary.iloc[top_n:]['Orders'].sum(),
                        'Profit Margin': (
                            team_summary.iloc[top_n:]['Profit'].sum() / team_summary.iloc[top_n:]['Revenue'].sum()
                            if team_summary.iloc[top_n:]['Revenue'].sum() != 0
                            else 0
                        ),
                        'SalesTeamFilter': '',
                    }
                ]
            )
            team_chart_df = pd.concat([team_summary.head(top_n), other], ignore_index=True)
        else:
            team_chart_df = team_summary.copy()
    else:
        team_chart_df = pd.DataFrame()

    channel_summary = (
        filtered_df.groupby('SalesChannel', dropna=False)
        .agg({'Transaction Amount': 'sum', 'Profit': 'sum', 'OrderQuantity': 'sum'})
        .rename(columns={'Transaction Amount': 'Revenue'})
        .reset_index()
        if 'SalesChannel' in filtered_df.columns
        else pd.DataFrame()
    )
    channel_order_definition = 'Total Orders uses transaction row count because a unique Order ID field was not available.'
    if not channel_summary.empty:
        if order_id_col and order_id_col in filtered_df.columns:
            channel_orders = filtered_df.groupby('SalesChannel', dropna=False)[order_id_col].nunique().rename('Orders').reset_index()
            channel_order_definition = f'Total Orders is based on distinct {order_id_col} values.'
        else:
            channel_orders = filtered_df.groupby('SalesChannel', dropna=False).size().rename('Orders').reset_index()
        channel_summary = channel_summary.merge(channel_orders, on='SalesChannel', how='left')
        channel_summary['Profit Margin'] = channel_summary['Profit'] / channel_summary['Revenue']
        channel_summary['Average Order Value'] = channel_summary['Revenue'] / channel_summary['Orders']
        channel_summary['Profit For Sizing'] = channel_summary['Profit'].clip(lower=0) + 1
        revenue_order = channel_summary.sort_values('Revenue', ascending=False)['SalesChannel'].tolist()
        channel_summary['SalesChannel'] = pd.Categorical(channel_summary['SalesChannel'], categories=revenue_order, ordered=True)
        channel_summary = channel_summary.sort_values('SalesChannel')

    map_df = pd.DataFrame()
    has_geographic_map = False
    map_note = ''
    if {'StateCode', 'State', 'Region'}.issubset(set(filtered_df.columns)):
        map_df = (
            filtered_df.groupby(['StateCode', 'State', 'Region'], dropna=False)
            .agg({'Transaction Amount': 'sum', 'Profit': 'sum'})
            .rename(columns={'Transaction Amount': 'Revenue'})
            .reset_index()
        )
        if not map_df.empty:
            map_orders = filtered_df.groupby(['StateCode', 'State', 'Region'], dropna=False).size().rename('Orders').reset_index()
            map_df = map_df.merge(map_orders, on=['StateCode', 'State', 'Region'], how='left')
            map_df['Profit Margin'] = map_df['Profit'] / map_df['Revenue']
            has_geographic_map = True
            map_note = 'Map uses state-level geography from Store Locations and Regions worksheets; color intensity represents revenue.'
    if not has_geographic_map:
        map_note = 'A true geographic choropleth was not possible from the available fields, so no map is displayed.'

    channel_insight = ''
    if not channel_summary.empty:
        high_volume_channel = channel_summary.sort_values('Orders', ascending=False).iloc[0]
        high_revenue_channel = channel_summary.sort_values('Revenue', ascending=False).iloc[0]
        weak_margin_channel = channel_summary.sort_values('Profit Margin', ascending=True).iloc[0]
        channel_insight = (
            f"{high_volume_channel['SalesChannel']} has the highest order volume ({high_volume_channel['Orders']:,.0f}), "
            f"while {high_revenue_channel['SalesChannel']} leads revenue (${high_revenue_channel['Revenue']:,.0f}). "
            f"{weak_margin_channel['SalesChannel']} shows the weakest margin at {weak_margin_channel['Profit Margin']:.1%}. "
            f"{channel_order_definition}"
        )

    team_chart_note = (
        'Chart displays top 10 teams by revenue with remaining teams grouped into Other for readability.'
        if not team_chart_df.empty and len(team_summary) > len(team_chart_df)
        else 'Chart displays all teams ranked by revenue.'
    )

    storyline_notes = _build_storyline_notes(analysis.region_revenue, team_summary, channel_summary, has_geographic_map)
    monthly_perf_df, benchmark_label = _prepare_monthly_performance_df(filtered_df)
    monthly_performance_insight = _monthly_performance_insight(monthly_perf_df, benchmark_label)

    charts = {
        'region_revenue': bar_chart(analysis.region_revenue, analysis.region_revenue.columns[0], 'Transaction Amount', 'Revenue by Region', chart_id='chart_region_revenue', customdata=analysis.region_revenue[analysis.region_revenue.columns[0]].tolist()) if not analysis.region_revenue.empty else '',
        'region_profit': bar_chart(analysis.region_profit, analysis.region_profit.columns[0], 'Profit', 'Profit by Region', chart_id='chart_region_profit', customdata=analysis.region_profit[analysis.region_profit.columns[0]].tolist()) if not analysis.region_profit.empty else '',
        'region_margin': bar_chart(analysis.region_margin, analysis.region_margin.columns[0], 'Profit Margin', 'Profit Margin by Region', chart_id='chart_region_margin', customdata=analysis.region_margin[analysis.region_margin.columns[0]].tolist()) if not analysis.region_margin.empty else '',
        'region_map': regional_revenue_map(map_df, 'Regional Revenue Intensity Map (US States)', chart_id='chart_region_map') if has_geographic_map else '',
        'channel_revenue': bar_chart(analysis.channel_revenue, analysis.channel_revenue.columns[0], 'Transaction Amount', 'Revenue by Sales Channel', chart_id='chart_channel_revenue', customdata=analysis.channel_revenue[analysis.channel_revenue.columns[0]].tolist()) if not analysis.channel_revenue.empty else '',
        'channel_profit': bar_chart(analysis.channel_profit, analysis.channel_profit.columns[0], 'Profit', 'Profit by Sales Channel', chart_id='chart_channel_profit', customdata=analysis.channel_profit[analysis.channel_profit.columns[0]].tolist()) if not analysis.channel_profit.empty else '',
        'channel_orders': channel_orders_bar_chart(channel_summary, 'Orders by Sales Channel', chart_id='chart_channel_orders') if not channel_summary.empty else '',
        'channel_margin': bar_chart(analysis.channel_margin, analysis.channel_margin.columns[0], 'Profit Margin', 'Profit Margin by Sales Channel', chart_id='chart_channel_margin', customdata=analysis.channel_margin[analysis.channel_margin.columns[0]].tolist()) if not analysis.channel_margin.empty else '',
        'channel_scatter': channel_orders_revenue_scatter(channel_summary, 'Orders and Revenue by Sales Channel', chart_id='chart_channel_scatter') if not channel_summary.empty else '',
        'customer_revenue': bar_chart(analysis.top_customers, 'CustomerName', 'Transaction Amount', 'Top Customers by Revenue', chart_id='chart_customer_revenue', orientation='h') if not analysis.top_customers.empty else '',
        'customer_profit': bar_chart(analysis.top_customers.sort_values('Profit', ascending=False), 'CustomerName', 'Profit', 'Top Customers by Profit', chart_id='chart_customer_profit', orientation='h') if not analysis.top_customers.empty else '',
        'team_revenue': sales_team_performance_chart(team_chart_df, 'Top Sales Teams by Revenue', chart_id='chart_sales_team') if not team_chart_df.empty else '',
        'team_profit': bar_chart(analysis.team_profit, analysis.team_profit.columns[0], 'Profit', 'Profit by Sales Team', chart_id='chart_team_profit', customdata=analysis.team_profit[analysis.team_profit.columns[0]].tolist()) if not analysis.team_profit.empty else '',
        'team_scatter': sales_team_scatter(team_summary, 'Orders and Revenue by Sales Team', chart_id='chart_team_scatter') if not team_summary.empty else '',
        'monthly_revenue': executive_monthly_performance_chart(monthly_perf_df, 'Monthly Revenue and Profit Performance', chart_id='chart_monthly_revenue', benchmark_label=benchmark_label) if not monthly_perf_df.empty else '',
        'monthly_revenue_exec': executive_monthly_performance_chart(monthly_perf_df, 'Monthly Revenue and Profit Performance', chart_id='chart_monthly_revenue_exec', benchmark_label=benchmark_label) if not monthly_perf_df.empty else '',
        'monthly_profit': line_chart(analysis.monthly, 'OrderMonth', 'Profit', 'Monthly Profit', chart_id='chart_monthly_profit') if not analysis.monthly.empty else '',
        'monthly_growth': growth_trend_chart(analysis.monthly, 'OrderMonth', 'Revenue Growth', 'Profit Growth', 'Monthly Revenue and Profit Growth', chart_id='chart_monthly_growth') if not analysis.monthly.empty else '',
        'quarterly_mix': combo_chart(analysis.quarterly, 'Quarter', 'Transaction Amount', 'Profit', 'Quarterly Revenue and Profit', chart_id='chart_quarterly_mix') if not analysis.quarterly.empty else '',
        'quarterly_mix_exec': combo_chart(analysis.quarterly, 'Quarter', 'Transaction Amount', 'Profit', 'Quarterly Revenue and Profit', chart_id='chart_quarterly_mix_exec') if not analysis.quarterly.empty else '',
        'customer_concentration': donut_chart(analysis.customer_concentration.head(10), 'CustomerName', 'Transaction Amount', 'Customer Revenue Concentration', chart_id='chart_customer_concentration') if not analysis.customer_concentration.empty else '',
        'product_revenue': bar_chart(analysis.product_revenue, analysis.product_revenue.columns[0], 'Transaction Amount', 'Revenue by Product', chart_id='chart_product_revenue') if has_product and analysis.product_revenue is not None and not analysis.product_revenue.empty else '',
        'product_profit': bar_chart(analysis.product_profit, analysis.product_profit.columns[0], 'Profit', 'Profit by Product', chart_id='chart_product_profit') if has_product and analysis.product_profit is not None and not analysis.product_profit.empty else '',
        'product_quantity': bar_chart(analysis.product_quantity, analysis.product_quantity.columns[0], 'OrderQuantity', 'Quantity by Product', chart_id='chart_product_quantity') if has_product and analysis.product_quantity is not None and not analysis.product_quantity.empty else '',
        'heatmap': heatmap(filtered_df, 'SalesChannel', 'Region', 'Transaction Amount', 'Revenue Heatmap: Region x Channel', chart_id='chart_heatmap') if 'Region' in filtered_df.columns else '',
        'scatter': scatter_plot(filtered_df.groupby('OrderDate').agg({'Transaction Amount': 'sum', 'Profit': 'sum'}).reset_index(), 'Transaction Amount', 'Profit', 'Revenue vs Profit', chart_id='chart_revenue_profit_scatter') if not filtered_df.empty else '',
        'box': box_plot(filtered_df, 'SalesChannel', 'Profit Margin', 'Profit Margin Distribution by Channel', chart_id='chart_box_channel_margin') if 'Profit Margin' in filtered_df.columns else '',
    }

    report_html = template.render(
        title='Regional Sales Business Intelligence Report',
        logo_data_uri=_build_logo_data_uri(project_dir),
        workbook_info=workbook_info,
        profile=profile,
        kpi_cards=kpi_cards(kpi_dict),
        summary=summary,
        top_insights=top_insights,
        storyline_notes=storyline_notes,
        business_problems=business_problems,
        map_note=map_note,
        channel_scatter_insight=channel_insight,
        channel_order_definition=channel_order_definition,
        team_chart_note=team_chart_note,
        monthly_performance_insight=monthly_performance_insight,
        monthly_benchmark_method=benchmark_label,
        quality_results=quality_results,
        charts=charts,
        has_product=has_product,
        revenue_by_region=ranked_table_html(analysis.region_revenue),
        profit_by_region=ranked_table_html(analysis.region_profit),
        revenue_by_channel=ranked_table_html(analysis.channel_revenue),
        team_rank=ranked_table_html(analysis.team_profit),
        top_customers=ranked_table_html(analysis.top_customers),
        bottom_customers=ranked_table_html(analysis.bottom_customers),
        concentration_table=ranked_table_html(analysis.customer_concentration),
        filter_records=filter_records.to_dict(orient='records'),
        filter_options=filter_options,
        corporate_theme=CORPORATE_THEME,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_html, encoding='utf-8')
    return output_path

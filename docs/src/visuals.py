from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .theme import (
    BENCHMARK_COLOR,
    INFO_COLOR,
    MARGIN_COLOR,
    MARGIN_COLORSCALE,
    ORDERS_COLOR,
    PROFIT_COLOR,
    PROFIT_COLORSCALE,
    REVENUE_COLOR,
    REVENUE_COLORSCALE,
    SCATTER_CATEGORICAL_COLORS,
    SCATTER_CONTINUOUS_SCALE,
    WARNING_COLOR,
)


def _metric_color(metric_name: str | None, default: str = REVENUE_COLOR) -> str:
    if metric_name in {'Transaction Amount', 'Revenue'}:
        return REVENUE_COLOR
    if metric_name == 'Profit':
        return PROFIT_COLOR
    if metric_name in {'Profit Margin', 'Margin'}:
        return MARGIN_COLOR
    return default


def _base_layout(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    fig.update_layout(
        title=title,
        template='plotly_white',
        margin=dict(l=30, r=20, t=60, b=30),
        height=height,
        legend_title_text='',
    )
    fig.update_xaxes(tickangle=0, showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def _to_html(fig: go.Figure, chart_id: str) -> str:
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=chart_id,
        config={'responsive': True, 'displaylogo': False},
    )


def _compact_currency(value: float) -> str:
    magnitude = abs(float(value))
    if magnitude >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if magnitude >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if magnitude >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def kpi_cards(kpis: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {'label': 'Total Revenue', 'value': f"${kpis['total_revenue']:,.0f}", 'note': 'Transaction Amount'},
        {'label': 'Total Profit', 'value': f"${kpis['total_profit']:,.0f}", 'note': 'Net profit after cost'},
        {'label': 'Profit Margin', 'value': f"{kpis['profit_margin']:.1%}", 'note': 'Profit / Revenue'},
        {'label': 'Total Orders', 'value': f"{kpis['total_orders']:,.0f}", 'note': 'Transaction count'},
        {'label': 'Total Customers', 'value': f"{kpis['total_customers']:,.0f}", 'note': 'Unique customers'},
        {'label': 'Total Sales Teams', 'value': f"{kpis['total_sales_teams']:,.0f}", 'note': 'Unique teams'},
        {'label': 'Average Order Value', 'value': f"${kpis['average_order_value']:,.0f}", 'note': 'Revenue / order'},
        {'label': 'Average Profit per Order', 'value': f"${kpis['average_profit_per_order']:,.0f}", 'note': 'Profit / order'},
    ]


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    chart_id: str,
    orientation: str = 'v',
    color: str | None = None,
    customdata: list[Any] | None = None,
) -> str:
    fig = go.Figure()
    resolved_color = color if color else _metric_color(y)
    value_format = '$,.0f' if y in {'Transaction Amount', 'Profit'} else '.1%'
    if orientation == 'v':
        fig.add_bar(
            x=df[x],
            y=df[y],
            marker_color=resolved_color,
            customdata=customdata,
            hovertemplate=f"%{{x}}<br>%{{y:{value_format}}}<extra></extra>",
        )
        fig.update_xaxes(title_text=x)
        fig.update_yaxes(title_text=y)
        if y in {'Transaction Amount', 'Profit'}:
            fig.update_yaxes(tickprefix='$', tickformat='~s')
    else:
        fig.add_bar(
            x=df[y],
            y=df[x],
            orientation='h',
            marker_color=resolved_color,
            customdata=customdata,
            hovertemplate=f"%{{y}}<br>%{{x:{value_format}}}<extra></extra>",
        )
        fig.update_xaxes(title_text=y)
        fig.update_yaxes(title_text=x)
        if y in {'Transaction Amount', 'Profit'}:
            fig.update_xaxes(tickprefix='$', tickformat='~s')
    return _to_html(_base_layout(fig, title), chart_id)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, chart_id: str, color: str | None = None) -> str:
    fig = go.Figure()
    resolved_color = color if color else _metric_color(y)
    fig.add_trace(go.Scatter(x=df[x], y=df[y], mode='lines+markers', line=dict(color=resolved_color, width=3), hovertemplate='%{x}<br>%{y:,.0f}<extra></extra>'))
    fig.update_traces(
        line_shape='spline',
        line=dict(width=3),
        marker=dict(size=7),
        connectgaps=True,
        selector=dict(type='scatter'),
    )
    if pd.api.types.is_datetime64_any_dtype(df[x]):
        fig.update_xaxes(title_text=x, tickformat='%b %Y')
    else:
        fig.update_xaxes(title_text=x)
    fig.update_yaxes(title_text=y)
    if y in {'Transaction Amount', 'Profit'}:
        fig.update_yaxes(tickprefix='$', tickformat='~s')
    return _to_html(_base_layout(fig, title), chart_id)


def executive_monthly_performance_chart(df: pd.DataFrame, title: str, chart_id: str, benchmark_label: str) -> str:
    custom = df[['Revenue', 'Profit', 'Profit Margin', 'Orders', 'Average Order Value', 'Revenue Diff Benchmark', 'Profit Diff Prev']].values
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df['OrderMonth'],
            y=df['Revenue'],
            mode='lines+markers',
            name='Monthly Revenue',
            line=dict(color=REVENUE_COLOR, width=3, dash='solid', smoothing=0.85),
            marker=dict(size=7),
            line_shape='spline',
            connectgaps=True,
            customdata=custom,
            hovertemplate=(
                'Month: %{x|%b %Y}<br>'
                'Revenue: $%{customdata[0]:,.0f}<br>'
                'Profit: $%{customdata[1]:,.0f}<br>'
                'Profit Margin: %{customdata[2]:.1%}<br>'
                'Order Count: %{customdata[3]:,.0f}<br>'
                'Average Order Value: $%{customdata[4]:,.0f}<br>'
                'Revenue vs Benchmark: $%{customdata[5]:+,.0f}<br>'
                'Profit vs Previous Month: $%{customdata[6]:+,.0f}<extra></extra>'
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df['OrderMonth'],
            y=df['Profit'],
            mode='lines+markers',
            name='Monthly Profit',
            line=dict(color=PROFIT_COLOR, width=3, dash='solid', smoothing=0.85),
            marker=dict(size=7),
            line_shape='spline',
            connectgaps=True,
            customdata=custom,
            hovertemplate=(
                'Month: %{x|%b %Y}<br>'
                'Revenue: $%{customdata[0]:,.0f}<br>'
                'Profit: $%{customdata[1]:,.0f}<br>'
                'Profit Margin: %{customdata[2]:.1%}<br>'
                'Order Count: %{customdata[3]:,.0f}<br>'
                'Average Order Value: $%{customdata[4]:,.0f}<br>'
                'Revenue vs Benchmark: $%{customdata[5]:+,.0f}<br>'
                'Profit vs Previous Month: $%{customdata[6]:+,.0f}<extra></extra>'
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df['OrderMonth'],
            y=df['Benchmark'],
            mode='lines',
            name=benchmark_label,
            line=dict(color=BENCHMARK_COLOR, width=2, dash='dash'),
            hovertemplate='Month: %{x|%b %Y}<br>Benchmark: $%{y:,.0f}<extra></extra>',
        )
    )

    annotations: list[dict[str, Any]] = []
    if not df.empty:
        points = [
            ('Highest Revenue Month', df['Revenue'].idxmax(), 'Revenue'),
            ('Lowest Revenue Month', df['Revenue'].idxmin(), 'Revenue'),
            ('Highest Profit Month', df['Profit'].idxmax(), 'Profit'),
            ('Lowest Profit Month', df['Profit'].idxmin(), 'Profit'),
        ]
        for label, idx, metric in points:
            row = df.loc[idx]
            annotations.append(
                dict(
                    x=row['OrderMonth'],
                    y=row[metric],
                    text=label,
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=-28,
                    bgcolor='rgba(255,255,255,0.8)',
                    font=dict(size=10),
                )
            )

        high_over = df[df['Revenue'] > (df['Benchmark'] * 1.10)]
        for _, row in high_over.iterrows():
            annotations.append(
                dict(
                    x=row['OrderMonth'],
                    y=row['Revenue'],
                    text='Rev > benchmark +10%',
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-16,
                    font=dict(size=9, color=REVENUE_COLOR),
                )
            )

        low_margin_cutoff = df['Profit Margin'].quantile(0.2)
        low_margin = df[df['Profit Margin'] < low_margin_cutoff]
        for _, row in low_margin.iterrows():
            annotations.append(
                dict(
                    x=row['OrderMonth'],
                    y=row['Profit'],
                    text='Low margin',
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=16,
                    font=dict(size=9, color=WARNING_COLOR),
                )
            )

    fig.update_layout(
        hovermode='x unified',
        annotations=annotations,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )
    fig.update_xaxes(title_text='Month', tickformat='%b %Y')
    fig.update_yaxes(title_text='Revenue / Profit', tickprefix='$', tickformat='~s')
    return _to_html(_base_layout(fig, title), chart_id)


def combo_chart(df: pd.DataFrame, x: str, y1: str, y2: str, title: str, chart_id: str) -> str:
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Bar(x=df[x], y=df[y1], name=y1, marker_color=_metric_color(y1), hovertemplate='%{x}<br>%{y:,.0f}<extra></extra>'), secondary_y=False)
    fig.add_trace(go.Scatter(x=df[x], y=df[y2], name=y2, mode='lines+markers', line=dict(color=_metric_color(y2), width=3), hovertemplate='%{x}<br>%{y:,.0f}<extra></extra>'), secondary_y=True)
    fig.update_traces(
        line_shape='spline',
        line=dict(width=3),
        marker=dict(size=7),
        connectgaps=True,
        selector=dict(type='scatter'),
    )
    fig.update_yaxes(title_text=y1, secondary_y=False)
    fig.update_yaxes(title_text=y2, secondary_y=True)
    if pd.api.types.is_datetime64_any_dtype(df[x]):
        fig.update_xaxes(title_text=x, tickformat='%b %Y')
    else:
        fig.update_xaxes(title_text=x)
    fig.update_yaxes(tickprefix='$', tickformat='~s', secondary_y=False)
    fig.update_yaxes(tickprefix='$', tickformat='~s', secondary_y=True)
    return _to_html(_base_layout(fig, title), chart_id)


def donut_chart(df: pd.DataFrame, names: str, values: str, title: str, chart_id: str) -> str:
    fig = go.Figure(data=[go.Pie(labels=df[names], values=df[values], hole=0.45, textinfo='label+percent', hovertemplate='%{label}<br>%{value:,.0f}<extra></extra>')])
    return _to_html(_base_layout(fig, title), chart_id)


def heatmap(df: pd.DataFrame, x: str, y: str, z: str, title: str, chart_id: str) -> str:
    pivot = df.pivot_table(index=y, columns=x, values=z, aggfunc='sum', fill_value=0)
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.astype(str),
            y=pivot.index.astype(str),
            colorscale=REVENUE_COLORSCALE,
            colorbar=dict(title='Revenue'),
            hovertemplate='%{y}<br>%{x}<br>$%{z:,.0f}<extra></extra>',
        )
    )
    return _to_html(_base_layout(fig, title), chart_id)


def scatter_plot(df: pd.DataFrame, x: str, y: str, title: str, chart_id: str) -> str:
    # Markers are colored by revenue value using Viridis: deep purple (low) → teal → bright yellow (high).
    positive = df[df[y] >= 0]
    negative = df[df[y] < 0]
    traces: list[go.BaseTraceType] = []
    if not positive.empty:
        traces.append(
            go.Scatter(
                x=positive[x],
                y=positive[y],
                mode='markers',
                name='Profit',
                marker=dict(
                    size=9,
                    opacity=0.85,
                    color=positive[x],
                    colorscale=SCATTER_CONTINUOUS_SCALE,
                    showscale=True,
                    colorbar=dict(title='Revenue', tickprefix='$', tickformat='~s'),
                    line=dict(color='white', width=0.4),
                ),
                hovertemplate='Revenue: $%{x:,.0f}<br>Profit: $%{y:,.0f}<extra></extra>',
            )
        )
    if not negative.empty:
        traces.append(
            go.Scatter(
                x=negative[x],
                y=negative[y],
                mode='markers',
                name='Negative Profit',
                marker=dict(
                    size=9,
                    opacity=0.85,
                    color=WARNING_COLOR,
                    line=dict(color='white', width=0.4),
                ),
                hovertemplate='Revenue: $%{x:,.0f}<br>Profit: $%{y:,.0f}<extra></extra>',
            )
        )
    fig = go.Figure(data=traces)
    fig.update_xaxes(title_text=None, tickprefix='$', tickformat='~s')
    fig.update_yaxes(title_text=None, tickprefix='$', tickformat='~s')
    return _to_html(_base_layout(fig, title), chart_id)


def box_plot(df: pd.DataFrame, x: str, y: str, title: str, chart_id: str) -> str:
    fig = go.Figure()
    fig.add_trace(go.Box(x=df[x], y=df[y], boxmean=True, marker_color=_metric_color(y)))
    return _to_html(_base_layout(fig, title), chart_id)


def regional_revenue_map(df: pd.DataFrame, title: str, chart_id: str) -> str:
    fig = go.Figure(
        data=go.Choropleth(
            locations=df['StateCode'],
            z=df['Revenue'],
            locationmode='USA-states',
            colorscale=REVENUE_COLORSCALE,
            marker_line_color='white',
            marker_line_width=1,
            customdata=df[['Region', 'Revenue', 'Profit', 'Profit Margin', 'Orders']].values,
            hovertemplate=(
                '<b>%{location}</b><br>'
                'Region: %{customdata[0]}<br>'
                'Revenue: $%{customdata[1]:,.0f}<br>'
                'Profit: $%{customdata[2]:,.0f}<br>'
                'Profit Margin: %{customdata[3]:.1%}<br>'
                'Orders: %{customdata[4]:,.0f}<extra></extra>'
            ),
            colorbar=dict(title='Revenue'),
        )
    )
    fig.update_layout(
        geo=dict(scope='usa', showlakes=True, lakecolor='rgb(255, 255, 255)'),
    )
    return _to_html(_base_layout(fig, title, height=480), chart_id)


def sales_team_performance_chart(df: pd.DataFrame, title: str, chart_id: str) -> str:
    chart_height = max(420, 80 + (len(df) * 36))
    fig = go.Figure(
        data=go.Bar(
            x=df['Revenue'],
            y=df['SalesTeam'],
            orientation='h',
            marker_color=REVENUE_COLOR,
            customdata=df[['SalesTeamFilter', 'Profit', 'Profit Margin', 'Orders', 'OrderQuantity']].values,
            text=df['Revenue'].map(_compact_currency),
            textposition='outside',
            cliponaxis=False,
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Revenue: $%{x:,.0f}<br>'
                'Profit: $%{customdata[1]:,.0f}<br>'
                'Profit Margin: %{customdata[2]:.1%}<br>'
                'Orders: %{customdata[3]:,.0f}<br>'
                'Order Quantity: %{customdata[4]:,.0f}<extra></extra>'
            ),
        )
    )
    fig.update_yaxes(autorange='reversed')
    fig.update_xaxes(title_text='Revenue', tickprefix='$', tickformat='~s')
    return _to_html(_base_layout(fig, title, height=chart_height), chart_id)


def channel_orders_revenue_scatter(df: pd.DataFrame, title: str, chart_id: str) -> str:
    max_profit = float(df['Profit For Sizing'].max()) if not df.empty else 0.0
    sizeref = (2.0 * max_profit / (54.0 ** 2)) if max_profit > 0 else 1.0
    unique_channels = df['SalesChannel'].astype(str).dropna().unique().tolist()
    category_color_map = {
        channel: SCATTER_CATEGORICAL_COLORS[index % len(SCATTER_CATEGORICAL_COLORS)]
        for index, channel in enumerate(unique_channels)
    }
    fig = go.Figure(
        data=go.Scatter(
            x=df['Orders'],
            y=df['Revenue'],
            mode='markers+text',
            text=df['SalesChannel'],
            textposition='top center',
            marker=dict(
                size=df['Profit For Sizing'],
                sizemode='area',
                sizeref=sizeref,
                sizemin=12,
                color=[category_color_map.get(str(channel), INFO_COLOR) for channel in df['SalesChannel']],
            ),
            customdata=df[['SalesChannel', 'OrderQuantity', 'Profit', 'Profit Margin', 'Average Order Value']].values,
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                'Total Orders: %{x:,.0f}<br>'
                'Order Quantity: %{customdata[1]:,.0f}<br>'
                'Revenue: $%{y:,.0f}<br>'
                'Profit: $%{customdata[2]:,.0f}<br>'
                'Profit Margin: %{customdata[3]:.1%}<br>'
                'Average Order Value: $%{customdata[4]:,.0f}<extra></extra>'
            ),
        )
    )
    fig.update_xaxes(title_text='Total Orders')
    fig.update_yaxes(title_text='Total Revenue', tickprefix='$', tickformat='~s')
    return _to_html(_base_layout(fig, title), chart_id)


def channel_orders_bar_chart(df: pd.DataFrame, title: str, chart_id: str) -> str:
    fig = go.Figure(
        data=go.Bar(
            x=df['SalesChannel'],
            y=df['Orders'],
            marker_color=ORDERS_COLOR,
            customdata=df[['OrderQuantity', 'Revenue', 'Profit', 'Average Order Value']].values,
            hovertemplate=(
                '<b>%{x}</b><br>'
                'Total Orders: %{y:,.0f}<br>'
                'Total Order Quantity: %{customdata[0]:,.0f}<br>'
                'Revenue: $%{customdata[1]:,.0f}<br>'
                'Profit: $%{customdata[2]:,.0f}<br>'
                'Average Order Value: $%{customdata[3]:,.0f}<extra></extra>'
            ),
        )
    )
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(title_text=None)
    return _to_html(_base_layout(fig, title), chart_id)


def growth_trend_chart(df: pd.DataFrame, x: str, revenue_growth: str, profit_growth: str, title: str, chart_id: str) -> str:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x],
            y=df[revenue_growth],
            mode='lines+markers',
            name='Revenue Growth',
            line=dict(color=REVENUE_COLOR, width=3),
            hovertemplate='%{x}<br>Revenue Growth: %{y:.1%}<extra></extra>',
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df[x],
            y=df[profit_growth],
            mode='lines+markers',
            name='Profit Growth',
            line=dict(color=PROFIT_COLOR, width=3),
            hovertemplate='%{x}<br>Profit Growth: %{y:.1%}<extra></extra>',
        )
    )
    fig.update_traces(
        line_shape='spline',
        line=dict(width=3),
        marker=dict(size=7),
        connectgaps=True,
        selector=dict(type='scatter'),
    )
    if pd.api.types.is_datetime64_any_dtype(df[x]):
        fig.update_xaxes(title_text=x, tickformat='%b %Y')
    else:
        fig.update_xaxes(title_text=x)
    fig.update_yaxes(title_text='Growth Rate', tickformat='.0%')
    return _to_html(_base_layout(fig, title), chart_id)


def sales_team_scatter(df: pd.DataFrame, title: str, chart_id: str) -> str:
    max_profit = float(df['Profit For Sizing'].max()) if not df.empty else 0.0
    sizeref = (2.0 * max_profit / (54.0 ** 2)) if max_profit > 0 else 1.0
    fig = go.Figure(
        data=go.Scatter(
            x=df['Orders'],
            y=df['Revenue'],
            mode='markers+text',
            text=df['SalesTeam'],
            textposition='top center',
            marker=dict(
                size=df['Profit For Sizing'],
                sizemode='area',
                sizeref=sizeref,
                sizemin=10,
                color=df['Profit Margin'],
                colorscale=SCATTER_CONTINUOUS_SCALE,
                showscale=True,
                colorbar=dict(title='Profit Margin'),
            ),
            customdata=df[['SalesTeamFilter', 'Profit', 'Profit Margin', 'OrderQuantity']].values,
            hovertemplate=(
                '<b>%{text}</b><br>'
                'Orders: %{x:,.0f}<br>'
                'Revenue: $%{y:,.0f}<br>'
                'Profit: $%{customdata[1]:,.0f}<br>'
                'Profit Margin: %{customdata[2]:.1%}<br>'
                'Order Quantity: %{customdata[3]:,.0f}<extra></extra>'
            ),
        )
    )
    fig.update_xaxes(title_text='Total Orders')
    fig.update_yaxes(title_text='Total Revenue', tickprefix='$', tickformat='~s')
    return _to_html(_base_layout(fig, title), chart_id)


def ranked_table_html(df: pd.DataFrame, max_rows: int = 10) -> str:
    return df.head(max_rows).to_html(index=False, classes='table table-striped', border=0, float_format=lambda x: f'{x:,.2f}')

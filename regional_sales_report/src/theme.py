from __future__ import annotations

CORPORATE_THEME = {
    "revenue": "#2F7DBA",
    "profit": "#2CA02C",
    "profit_margin": "#FF7F0E",
    "benchmark": "#7F7F7F",
    "warning": "#D62728",
    "orders": "#FF7F0E",
    "info": "#CBD5E1",
    "revenue_colorscale": [
        [0.000, "#F2F8FD"],
        [0.143, "#D9ECFA"],
        [0.286, "#B7D8F5"],
        [0.429, "#8FC1EC"],
        [0.571, "#5EA6DF"],
        [0.714, "#2F7DBA"],
        [0.857, "#1F5F99"],
        [1.000, "#123F6B"],
    ],
    "profit_colorscale": [
        "#E8F6EE",
        "#CDEEDC",
        "#A8E0C1",
        "#79CFA0",
        "#4DBB82",
        "#2CA02C",
        "#1D7F24",
        "#145C1A",
    ],
    "margin_colorscale": [
        "#FFF3E6",
        "#FFE2BF",
        "#FFD199",
        "#FFBD73",
        "#FFA54A",
        "#FF8C1A",
        "#E67700",
        "#B85A00",
    ],
    "scatter_continuous_scale": "Viridis",
    "scatter_categorical_colors": [
        "#1F77B4",
        "#FF7F0E",
        "#2CA02C",
        "#9467BD",
        "#17BECF",
        "#8C564B",
        "#E377C2",
        "#7F7F7F",
    ],
}

REVENUE_COLOR = CORPORATE_THEME["revenue"]
PROFIT_COLOR = CORPORATE_THEME["profit"]
MARGIN_COLOR = CORPORATE_THEME["profit_margin"]
BENCHMARK_COLOR = CORPORATE_THEME["benchmark"]
WARNING_COLOR = CORPORATE_THEME["warning"]
ORDERS_COLOR = CORPORATE_THEME["orders"]
INFO_COLOR = CORPORATE_THEME["info"]
REVENUE_COLORSCALE = CORPORATE_THEME["revenue_colorscale"]
PROFIT_COLORSCALE = CORPORATE_THEME["profit_colorscale"]
MARGIN_COLORSCALE = CORPORATE_THEME["margin_colorscale"]
SCATTER_CONTINUOUS_SCALE = CORPORATE_THEME["scatter_continuous_scale"]
SCATTER_CATEGORICAL_COLORS = CORPORATE_THEME["scatter_categorical_colors"]

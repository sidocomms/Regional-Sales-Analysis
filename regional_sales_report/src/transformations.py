from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class PreparedData:
    orders: pd.DataFrame
    customers: pd.DataFrame
    store_locations: pd.DataFrame
    categories: pd.DataFrame
    regions: pd.DataFrame
    sales_teams: pd.DataFrame
    column_map: dict[str, str]
    has_product: bool


DEFAULT_COLUMN_CANDIDATES = {
    "order_id": ["OrderNumber", "Order ID", "OrderNumberID"],
    "sales_channel": ["SalesChannel", "Channel"],
    "warehouse_code": ["WarehouseCode", "Warehouse Code"],
    "order_date": ["OrderDate", "Order Date", "Date"],
    "ship_date": ["ShipDate", "Ship Date"],
    "delivery_date": ["DeliveryDate", "Delivery Date"],
    "currency_code": ["CurrencyCode", "Currency Code"],
    "sales_team_id": ["SalesTeamID", "Sales Team ID", "TeamID"],
    "customer_id": ["CustomerID", "Customer ID"],
    "store_id": ["StoreID", "Store ID"],
    "category_id": ["CategoryID", "Category ID", "ProductID", "Product ID"],
    "order_quantity": ["OrderQuantity", "Order Quantity", "Quantity"],
    "discount_applied": ["DiscountApplied", "Discount Applied", "Discount"],
    "unit_price": ["UnitPrice", "Unit Price", "Price"],
    "unit_cost": ["UnitCost", "Unit Cost", "Cost"],
}


def resolve_column_map(df: pd.DataFrame) -> dict[str, str]:
    columns = {column.lower().replace(" ", "").replace("_", ""): column for column in df.columns}
    resolved: dict[str, str] = {}
    for key, candidates in DEFAULT_COLUMN_CANDIDATES.items():
        found = None
        for candidate in candidates:
            normalized = candidate.lower().replace(" ", "").replace("_", "")
            if normalized in columns:
                found = columns[normalized]
                break
        if found:
            resolved[key] = found
    return resolved


def _safe_merge(left: pd.DataFrame, right: pd.DataFrame, on: str, suffix: str) -> pd.DataFrame:
    if on not in left.columns or on not in right.columns:
        return left
    return left.merge(right, on=on, how="left", suffixes=("", suffix))


def prepare_data(sheets: dict[str, pd.DataFrame]) -> PreparedData:
    orders = sheets["Sales Orders Sheet"].copy()
    customers = sheets.get("Customers Sheet", pd.DataFrame()).copy()
    store_locations = sheets.get("Store Locations Sheet", pd.DataFrame()).copy()
    categories = sheets.get("Categories Sheet", pd.DataFrame()).copy()
    regions = sheets.get("Regions Sheet", pd.DataFrame()).copy()
    sales_teams = sheets.get("Sales Team Sheet", pd.DataFrame()).copy()

    column_map = resolve_column_map(orders)
    for required in ["order_quantity", "unit_price", "unit_cost", "order_date"]:
        if required not in column_map:
            raise ValueError(f"Required column could not be mapped: {required}")

    orders = orders.copy()
    orders["OrderDate"] = pd.to_datetime(orders[column_map["order_date"]], errors="coerce")
    if column_map.get("ship_date"):
        orders["ShipDate"] = pd.to_datetime(orders[column_map["ship_date"]], errors="coerce")
    if column_map.get("delivery_date"):
        orders["DeliveryDate"] = pd.to_datetime(orders[column_map["delivery_date"]], errors="coerce")

    orders["OrderQuantity"] = pd.to_numeric(orders[column_map["order_quantity"]], errors="coerce")
    orders["UnitPrice"] = pd.to_numeric(orders[column_map["unit_price"]], errors="coerce")
    orders["UnitCost"] = pd.to_numeric(orders[column_map["unit_cost"]], errors="coerce")
    if column_map.get("discount_applied"):
        orders["DiscountApplied"] = pd.to_numeric(orders[column_map["discount_applied"]], errors="coerce")

    orders["Transaction Amount"] = orders["OrderQuantity"] * orders["UnitPrice"]
    orders["Total Cost"] = orders["OrderQuantity"] * orders["UnitCost"]
    orders["Profit"] = orders["Transaction Amount"] - orders["Total Cost"]
    orders["Profit Margin"] = orders["Profit"] / orders["Transaction Amount"]
    orders["Profit Margin"] = orders["Profit Margin"].replace([pd.NA, pd.NaT, float("inf"), float("-inf")], pd.NA)
    orders["OrderMonth"] = orders["OrderDate"].dt.to_period("M").dt.to_timestamp()
    orders["OrderQuarter"] = orders["OrderDate"].dt.to_period("Q").astype(str)
    orders["Year"] = orders["OrderDate"].dt.year
    orders["MonthLabel"] = orders["OrderDate"].dt.strftime("%Y-%m")

    if not customers.empty:
        orders = _safe_merge(orders, customers.rename(columns={"CustomerID": "CustomerID", "CustomerName": "CustomerName"}), "CustomerID", "_customer")
    if not sales_teams.empty:
        orders = _safe_merge(orders, sales_teams.rename(columns={"SalesTeamID": "SalesTeamID", "SalesTeam": "SalesTeam", "YearlySalesGoal": "YearlySalesGoal"}), "SalesTeamID", "_team")
    if not categories.empty:
        orders = _safe_merge(orders, categories.rename(columns={"CategoryID": "CategoryID", "Category": "Category"}), "CategoryID", "_category")
    if not store_locations.empty:
        orders = _safe_merge(orders, store_locations.rename(columns={"StoreID": "StoreID", "CityName": "CityName", "State": "State", "StateCode": "StateCode"}), "StoreID", "_store")
    if not regions.empty and "StateCode" in orders.columns:
        orders = orders.merge(regions, on=["StateCode", "State"], how="left")

    has_product = "Category" in orders.columns or "CategoryID" in orders.columns
    return PreparedData(
        orders=orders,
        customers=customers,
        store_locations=store_locations,
        categories=categories,
        regions=regions,
        sales_teams=sales_teams,
        column_map=column_map,
        has_product=has_product,
    )

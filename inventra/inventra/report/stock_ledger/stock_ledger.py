# Copyright (c) 2025, Kalutu and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters: dict | None = None):
    """Return columns and data for the report."""
    columns = get_columns()
    conditions = get_conditions(filters)
    rows = fetch_stock_ledger_entries(conditions, filters)
    data = process_stock_entries(rows)
    return columns, data


def get_columns() -> list[dict]:
    """Return columns for the Stock Ledger report."""
    return [
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": _("Qty In"), "fieldname": "qty_in", "fieldtype": "Float", "width": 80},
        {"label": _("Qty Out"), "fieldname": "qty_out", "fieldtype": "Float", "width": 80},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Float", "width": 100},
        {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 120},
        {"label": _("Avg Rate"), "fieldname": "avg_rate", "fieldtype": "Currency", "width": 120},
        {"label": _("Balance Value"), "fieldname": "balance_value", "fieldtype": "Currency", "width": 140},
        {"label": _("Stock Entry Reference"), "fieldname": "stock_entry_reference", "fieldtype": "Link", "options": "Stock Entry", "width": 180}
    ]


def get_conditions(filters: dict | None) -> str:
    """Build SQL WHERE conditions based on filters."""
    conditions = ["is_cancelled = 0"]

    if filters:
        if filters.get("from_date"):
            conditions.append("posting_date >= %(from_date)s")
        if filters.get("to_date"):
            conditions.append("posting_date <= %(to_date)s")
        if filters.get("item"):
            conditions.append("item = %(item)s")
        if filters.get("warehouse"):
            conditions.append("warehouse = %(warehouse)s")
        if filters.get("stock_entry_reference"):
            conditions.append("stock_entry_reference = %(stock_entry_reference)s")

    return " AND ".join(conditions)


def fetch_stock_ledger_entries(conditions: str, filters: dict | None) -> list[dict]:
    """Run SQL to fetch stock ledger entries."""
    return frappe.db.sql(f"""
        SELECT
            posting_date,
            item,
            warehouse,
            qty_change,
            valuation_rate,
            stock_entry_reference
        FROM
            `tabStock Ledger Entry`
        WHERE
            {conditions}
        ORDER BY
            posting_date ASC, warehouse ASC
    """, filters or {}, as_dict=True)


def process_stock_entries(rows: list[dict]) -> list[dict]:
    """Process stock ledger rows into report-ready format with balances and averages."""
    balances = {}
    avg_rates = {}
    data = []

    for row in rows:
        key = (row.item, row.warehouse)

        if key not in balances:
            balances[key] = 0
            avg_rates[key] = 0

        qty_in = row.qty_change if row.qty_change > 0 else 0
        qty_out = row.qty_change if row.qty_change < 0 else 0

        if qty_in > 0:
            total_value = (balances[key] * avg_rates[key]) + (qty_in * row.valuation_rate)
            new_qty = balances[key] + qty_in
            avg_rates[key] = total_value / new_qty if new_qty else 0

        balances[key] += row.qty_change
        balance_value = balances[key] * avg_rates[key]

        data.append({
            "posting_date": row.posting_date,
            "item": row.item,
            "warehouse": row.warehouse,
            "qty_in": qty_in,
            "qty_out": qty_out,
            "balance": balances[key],
            "avg_rate": avg_rates[key],
            "balance_value": balance_value,
            "valuation_rate": row.valuation_rate,
            "stock_entry_reference": row.stock_entry_reference
        })

    return data

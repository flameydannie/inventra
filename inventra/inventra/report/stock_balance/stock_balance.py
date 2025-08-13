# Copyright (c) 2025, Kalutu and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters: dict | None = None):
    """Main entry point for the Stock Balance report."""
    filters = filters or {}

    if not filters.get("to_date"):
        frappe.throw(_("Please set a 'To Date' filter."))

    # Normalize dates
    filters["from_date"] = getdate(filters["from_date"]) if filters.get("from_date") else None
    filters["to_date"] = getdate(filters["to_date"])

    columns = get_columns()
    sle_rows = get_sle(filters)
    data = calculate_balances(sle_rows, filters)

    return columns, data


def get_columns():
    """Define report columns."""
    return [
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": _("Opening Qty"), "fieldname": "opening_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Opening Value"), "fieldname": "opening_value", "fieldtype": "Currency", "options": "Currency", "width": 140},
        {"label": _("In Qty"), "fieldname": "in_qty", "fieldtype": "Float", "width": 100},
        {"label": _("In Value"), "fieldname": "in_value", "fieldtype": "Currency", "options": "Currency", "width": 140},
        {"label": _("Out Qty"), "fieldname": "out_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Out Value"), "fieldname": "out_value", "fieldtype": "Currency", "options": "Currency", "width": 140},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Balance Value"), "fieldname": "balance_value", "fieldtype": "Currency", "options": "Currency", "width": 140},
        {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "options": "Currency", "width": 120},
    ]


def get_sle(filters):
    """Fetch stock ledger entries filtered by item, warehouse, and date."""
    conditions = ["is_cancelled = 0", "posting_date <= %(to_date)s"]

    if filters.get("item"):
        conditions.append("item = %(item)s")
    if filters.get("warehouse"):
        conditions.append("warehouse = %(warehouse)s")

    where_clause = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT posting_date, item, warehouse, qty_change, valuation_rate
        FROM `tabStock Ledger Entry`
        WHERE {where_clause}
        ORDER BY posting_date ASC
        """,
        filters,
        as_dict=True
    )


def calculate_balances(rows, filters):
    """Compute opening balances, movements, and closing balances."""
    from_date = filters.get("from_date")

    balances = {}
    openings = {}
    movements = {}

    def init_item_record(key):
        """Ensure dict entries exist for the given (item, warehouse) key."""
        if key not in balances:
            balances[key] = {"qty": 0.0, "value": 0.0}
            openings[key] = {"qty": 0.0, "value": 0.0}
            movements[key] = {"in_qty": 0.0, "in_val": 0.0, "out_qty": 0.0, "out_val": 0.0}

    for row in rows:
        key = (row.item, row.warehouse)
        init_item_record(key)

        qty_change = flt(row.qty_change)
        rate = flt(row.valuation_rate)
        bal = balances[key]

        # Before reporting period → opening balance
        if from_date and row.posting_date < from_date:
            bal["qty"] += qty_change
            bal["value"] += qty_change * rate
            openings[key] = bal.copy()
            continue

        # Within reporting period → movements
        if qty_change > 0:  # Inbound
            value_in = qty_change * rate
            bal["qty"] += qty_change
            bal["value"] += value_in
            movements[key]["in_qty"] += qty_change
            movements[key]["in_val"] += value_in

        elif qty_change < 0:  # Outbound
            qty_out = abs(qty_change)
            avg_rate = bal["value"] / bal["qty"] if bal["qty"] else 0
            value_out = qty_out * avg_rate
            bal["qty"] -= qty_out
            bal["value"] -= value_out

            # Avoid floating-point residue
            if abs(bal["qty"]) < 1e-9:
                bal.update({"qty": 0.0, "value": 0.0})

            movements[key]["out_qty"] += qty_out
            movements[key]["out_val"] += value_out

    # Prepare report data
    data = []
    for (item, warehouse), bal in balances.items():
        o = openings[(item, warehouse)]
        m = movements[(item, warehouse)]
        valuation_rate = bal["value"] / bal["qty"] if bal["qty"] else 0.0

        data.append({
            "item": item,
            "warehouse": warehouse,
            "opening_qty": o["qty"],
            "opening_value": o["value"],
            "in_qty": m["in_qty"],
            "in_value": m["in_val"],
            "out_qty": m["out_qty"],
            "out_value": m["out_val"],
            "balance_qty": bal["qty"],
            "balance_value": bal["value"],
            "valuation_rate": valuation_rate,
        })

    return data

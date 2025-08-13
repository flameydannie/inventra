# Copyright (c) 2025, Kalutu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StockEntry(Document):
    def before_save(self):
        """Set valuation rates for items before saving (except for Receipts)."""
        if self.stock_entry_type != "Receipt":
            for row in self.items:
                item = row.item
                warehouse = row.source_warehouse
                row.valuation_rate = calculate_valuation_rate(item, warehouse)

    def on_submit(self):
        """Handle creation of stock ledger entries when submitting."""
        self.create_stock_ledger_entries()

    def on_cancel(self):
        """Handle deletion of stock ledger entries when canceling."""
        self.delete_stock_ledger_entries()

    def create_stock_ledger_entries(self):
        """Create stock ledger entries based on entry type."""
        for row in self.items:
            item = row.item
            valuation_rate = row.valuation_rate
            qty = row.qty
            source_warehouse = row.source_warehouse
            target_warehouse = row.target_warehouse

            if self.stock_entry_type == "Receipt":
                self.make_sle(item, target_warehouse, qty, valuation_rate)

            elif self.stock_entry_type in ("Consume", "Transfer"):
                self.make_sle(item, source_warehouse, -qty, valuation_rate)

                if self.stock_entry_type == "Transfer":
                    self.make_sle(item, target_warehouse, qty, valuation_rate)

    def make_sle(self, item, warehouse, qty, valuation_rate):
        """Create a single stock ledger entry."""
        frappe.get_doc({
            "doctype": "Stock Ledger Entry",
            "item": item,
            "warehouse": warehouse,
            "posting_date": self.posting_date,
            "qty_change": qty,
            "valuation_rate": valuation_rate,
            "stock_entry_reference": self.name
        }).insert()

    def delete_stock_ledger_entries(self):
        """Delete all stock ledger entries linked to this stock entry."""
        frappe.db.delete("Stock Ledger Entry", {
            "stock_entry_reference": self.name
        })


@frappe.whitelist()
def calculate_valuation_rate(item, warehouse):
    """Calculate average valuation rate for the given item and warehouse."""
    data = frappe.db.sql("""
        SELECT 
            SUM(qty_change) AS total_qty,
            SUM(qty_change * valuation_rate) AS total_value
        FROM `tabStock Ledger Entry`
        WHERE item = %s AND warehouse = %s
    """, (item, warehouse), as_dict=True)[0]

    total_qty = data.total_qty or 0
    total_value = data.total_value or 0

    return (total_value / total_qty) if total_qty else 0

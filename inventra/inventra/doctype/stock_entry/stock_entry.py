# Copyright (c) 2025, Kalutu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StockEntry(Document):
    def before_save(self):
        if self.entry_type != "Receipt":
            for item in self.items:
                item.valuation_rate = calculate_valuation_rate(item.item, self.source_warehouse)

    def on_submit(self):
        self.create_stock_ledger_entries()

    def on_cancel(self):
        self.delete_stock_ledger_entries()

    def create_stock_ledger_entries(self):
        """Create stock ledger entries based on entry type."""
        for item in self.items:
            if self.entry_type == "Receipt":
                self.make_sle(item.item, self.target_warehouse, item.qty, item.valuation_rate)

            elif self.entry_type in ("Consume", "Transfer"):
                self.make_sle(item.item, self.source_warehouse, -item.qty, item.valuation_rate)

                if self.entry_type == "Transfer":
                    self.make_sle(item.item, self.target_warehouse, item.qty, item.valuation_rate)

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

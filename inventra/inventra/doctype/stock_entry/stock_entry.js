// Copyright (c) 2025, Kalutu and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Entry", {
	entry_type(frm) {
		update_valuation_rates(frm);
	},
	source_warehouse(frm) {
		update_valuation_rates(frm);
	},
});

frappe.ui.form.on("Stock Entry Item", {
	item(frm, cdt, cdn) {
		update_valuation_rates(frm);
	},
});

function update_valuation_rates(frm) {
	if (!frm.doc || frm.doc.entry_type === "Receipt") return;

	const warehouse = frm.doc.source_warehouse;
	if (!warehouse) return;

	(frm.doc.items || []).forEach((row) => {
		if (row.item) {
			frappe.call({
				method: "inventra.inventra.doctype.stock_entry.stock_entry.calculate_valuation_rate",
				args: {
					item: row.item,
					warehouse: warehouse,
				},
				callback: function (r) {
					if (r.message !== undefined) {
						frappe.model.set_value(row.doctype, row.name, "valuation_rate", r.message);
					}
				},
			});
		}
	});
}

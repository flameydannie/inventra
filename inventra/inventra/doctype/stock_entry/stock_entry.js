// Copyright (c) 2025, Kalutu and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Entry", {
	stock_entry_type(frm) {
		update_valuation_rates(frm);
	},
});

frappe.ui.form.on("Stock Entry Item", {
	item(frm, cdt, cdn) {
		update_valuation_rates(frm);
	},
	source_warehouse(frm, cdt, cdn) {
		update_valuation_rates(frm);
	},
	qty(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.qty == 0) {
			frappe.model.set_value(cdt, cdn, "qty", "");
			frappe.msgprint({
				title: "Invalid Quantity",
				message: `Quantity for Item ${row.item} cannot be zero.`,
			});
		}
	},
});

function update_valuation_rates(frm) {
	if (!frm.doc || frm.doc.stock_entry_type === "Receipt") return;

	(frm.doc.items || []).forEach((row) => {
		const item = row.item;
		const warehouse = row.source_warehouse;

		if (item && warehouse) {
			frappe.call({
				method: "inventra.inventra.doctype.stock_entry.stock_entry.calculate_valuation_rate",
				args: { item, warehouse },
				callback: function (r) {
					if (r.message !== undefined) {
						frappe.model.set_value(row.doctype, row.name, "valuation_rate", r.message);
					}
				},
			});
		}
	});
}

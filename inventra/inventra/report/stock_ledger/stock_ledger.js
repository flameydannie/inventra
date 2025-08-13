// Copyright (c) 2025, Kalutu and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Ledger"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "item",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "stock_entry_reference",
			label: __("Stock Entry Reference"),
			fieldtype: "Link",
			options: "Stock Entry",
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "qty_in" && data?.qty_in > 0) {
			value = `<span style='color:green;'>${data.qty_in.toFixed(3)}</span>`;
		}
		if (column.fieldname === "qty_out" && data?.qty_out < 0) {
			value = `<span style='color:red;'>${data.qty_out.toFixed(3)}</span>`;
		}
		return value;
	},
};

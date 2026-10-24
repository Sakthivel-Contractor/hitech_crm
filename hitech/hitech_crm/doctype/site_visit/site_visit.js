// Copyright (c) 2026, Hitech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Site Visit", {
	refresh(frm) {
		if (frm.doc.map_link) {
			frm.add_custom_button(__("Open in Maps"), () => {
				window.open(frm.doc.map_link, "_blank", "noopener");
			});
		}

		if (frm.doc.lead) {
			frm.add_custom_button(__("View Lead"), () => {
				frappe.set_route("Form", "CRM Lead", frm.doc.lead);
			});
		}
	},
});

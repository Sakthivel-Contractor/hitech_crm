"""Fill Work Type on Facebook leads imported before the before_insert hook existed.

Those leads got the field default ("New Well") whatever the customer answered.
"""

import frappe

from hitech.facebook_leads import ANSWER_FIELD, WORK_TYPE_FIELD, work_type_for_answer, work_type_options


def execute():
	if not frappe.get_meta("CRM Lead").has_field(ANSWER_FIELD):
		return

	options = work_type_options()
	leads = frappe.get_all(
		"CRM Lead",
		filters={"source": "Facebook", ANSWER_FIELD: ["is", "set"]},
		fields=["name", ANSWER_FIELD, WORK_TYPE_FIELD],
	)
	for lead in leads:
		work_type = work_type_for_answer(lead[ANSWER_FIELD], options)
		if work_type != lead[WORK_TYPE_FIELD]:
			frappe.db.set_value("CRM Lead", lead.name, WORK_TYPE_FIELD, work_type, update_modified=False)

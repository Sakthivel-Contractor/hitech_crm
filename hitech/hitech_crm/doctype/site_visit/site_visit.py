# Copyright (c) 2026, Hitech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import format_datetime

SITE_VISIT_LEAD_STATUS = "Site Visit"


class SiteVisit(Document):
	def validate(self):
		self.validate_well_details()
		self.validate_location()
		self.set_map_link()

	def after_insert(self):
		self.add_note_to_lead()
		self.update_lead_status()

	def validate_well_details(self):
		for fieldname in ("diameter_ft", "expected_depth_ft", "rock_from_ft"):
			if (self.get(fieldname) or 0) < 0:
				frappe.throw(_("{0} cannot be negative").format(_(self.meta.get_label(fieldname))))

		# Only compare when an expected depth has been entered (0 means not set)
		if self.expected_depth_ft and (self.rock_from_ft or 0) > self.expected_depth_ft:
			frappe.throw(
				_("Rock Starts At ({0} ft) cannot be greater than Expected Depth ({1} ft)").format(
					self.rock_from_ft, self.expected_depth_ft
				)
			)

	def validate_location(self):
		if self.latitude and not -90 <= self.latitude <= 90:
			frappe.throw(_("Latitude must be between -90 and 90"))
		if self.longitude and not -180 <= self.longitude <= 180:
			frappe.throw(_("Longitude must be between -180 and 180"))

	def set_map_link(self):
		if self.latitude and self.longitude:
			self.map_link = f"https://maps.google.com/?q={self.latitude},{self.longitude}"
		else:
			self.map_link = None

	def add_note_to_lead(self):
		content = "<br>".join(
			[
				_("Visit Date: {0}").format(format_datetime(self.visit_date)),
				_("Soil Type: {0}").format(self.soil_type or "-"),
				_("Expected Depth: {0} ft").format(self.expected_depth_ft or "-"),
			]
		)
		frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": _("Site visit done"),
				"content": f"<p>{content}</p>",
				"reference_doctype": "CRM Lead",
				"reference_docname": self.lead,
			}
		).insert(ignore_permissions=True)

	def update_lead_status(self):
		if not frappe.db.exists("CRM Lead Status", SITE_VISIT_LEAD_STATUS):
			return

		lead = frappe.get_doc("CRM Lead", self.lead)
		if lead.status != SITE_VISIT_LEAD_STATUS:
			lead.status = SITE_VISIT_LEAD_STATUS
			lead.save(ignore_permissions=True)

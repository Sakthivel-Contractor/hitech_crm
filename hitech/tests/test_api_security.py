import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from hitech import api


class TestApiSecurity(unittest.TestCase):
	def test_public_lead_endpoint_only_allows_post(self):
		self.assertEqual(
			frappe.allowed_http_methods_for_whitelisted_func[api.create_website_lead],
			("POST",),
		)

	def test_device_registration_requires_lead_access(self):
		with patch.object(api, "frappe") as frappe, patch.object(api, "_", side_effect=lambda value: value):
			frappe.session.user = "website-user@example.com"
			frappe.has_permission.return_value = False
			frappe.PermissionError = PermissionError
			frappe.throw.side_effect = PermissionError("CRM Lead access required")

			with self.assertRaises(PermissionError):
				api.register_device("test-token", "android", "test-device")

			frappe.db.get_value.assert_not_called()

	def test_push_only_targets_users_with_access_to_the_lead(self):
		lead = SimpleNamespace(name="CRM-LEAD-TEST", lead_name="Test Lead")
		registrations = [
			SimpleNamespace(user="sales@example.com", token="sales-token"),
			SimpleNamespace(user="website@example.com", token="website-token"),
		]
		response = SimpleNamespace(success_count=1, failure_count=0)
		with (
			patch.object(api, "frappe") as frappe,
			patch.object(api, "_get_firebase_app"),
			patch.object(api, "_cleanup_invalid_tokens"),
			patch("firebase_admin.messaging.send_each_for_multicast", return_value=response) as send,
		):
			frappe.db.get_all.return_value = registrations
			frappe.has_permission.side_effect = lambda _doctype, **kwargs: (
				kwargs["user"] == "sales@example.com"
			)
			api.notify_new_lead(lead)

			self.assertEqual(send.call_args.args[0].tokens, ["sales-token"])
			self.assertEqual(frappe.has_permission.call_count, 2)

	def test_public_lead_rejects_invalid_phone_before_insert(self):
		create_lead = inspect.unwrap(api.create_website_lead)
		with patch.object(api, "frappe") as frappe, patch.object(api, "_", side_effect=lambda value: value):
			frappe.ValidationError = ValueError
			frappe.throw.side_effect = ValueError("Invalid phone")
			with self.assertRaises(ValueError):
				create_lead(name="Test Lead", phone="0000000000")
			frappe.get_doc.assert_not_called()


if __name__ == "__main__":
	unittest.main()

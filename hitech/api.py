# Copyright (c) 2026, Hitech and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# ---------------------------------------------------------------------------
# Firebase helpers
# ---------------------------------------------------------------------------

def _get_firebase_app():
	"""Return the already-initialised Firebase app, initialising it on first
	call per worker process."""
	import firebase_admin
	from firebase_admin import credentials

	if not firebase_admin._apps:
		service_account_path = frappe.get_site_path(
			"private", "files", "firebase_service_account.json"
		)
		cred = credentials.Certificate(service_account_path)
		firebase_admin.initialize_app(cred)

	return firebase_admin.get_app()


# ---------------------------------------------------------------------------
# Whitelisted API methods (called by the Flutter app)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def register_device(token: str, platform: str, device_name: str) -> dict:
	"""Save or update the FCM token for the currently logged-in user.

	Called by the Flutter app after a successful login::

	    POST /api/method/hitech.api.register_device
	    { "token": "...", "platform": "android", "device_name": "Pixel 7" }
	"""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)

	# Upsert: if this exact token already exists for any user, update it;
	# otherwise create a new record.
	existing = frappe.db.get_value(
		"HiTech Device Token", {"token": token}, "name"
	)

	if existing:
		doc = frappe.get_doc("HiTech Device Token", existing)
		doc.user = user
		doc.platform = platform
		doc.device_name = device_name
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.logger().info(f"[FCM] Updated device token for user={user} name={doc.name}")
	else:
		doc = frappe.get_doc(
			{
				"doctype": "HiTech Device Token",
				"user": user,
				"token": token,
				"platform": platform,
				"device_name": device_name,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.logger().info(f"[FCM] Registered new device token for user={user} name={doc.name}")

	return {"status": "ok", "name": doc.name}


@frappe.whitelist()
def unregister_device(token: str) -> dict:
	"""Delete the FCM token for the currently logged-in user.

	Called by the Flutter app on logout::

	    POST /api/method/hitech.api.unregister_device
	    { "token": "..." }
	"""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)

	existing = frappe.db.get_value(
		"HiTech Device Token", {"token": token, "user": user}, "name"
	)

	if existing:
		frappe.delete_doc("HiTech Device Token", existing, ignore_permissions=True)
		frappe.db.commit()
		frappe.logger().info(f"[FCM] Unregistered device token for user={user}")
		return {"status": "ok", "deleted": True}

	return {"status": "ok", "deleted": False}


# ---------------------------------------------------------------------------
# Internal hook handler (NOT whitelisted — triggered via hooks.py)
# ---------------------------------------------------------------------------


def notify_new_lead(doc, method=None) -> None:
	"""Send an FCM push notification to all registered devices when a new
	CRM Lead is created.

	Registered in hooks.py::

	    doc_events = {
	        "CRM Lead": {
	            "after_insert": "hitech.api.notify_new_lead"
	        }
	    }

	This function is intentionally wrapped in a broad try/except so that any
	Firebase failure never blocks lead creation.
	"""
	try:
		from firebase_admin import messaging

		# Collect all registered FCM tokens
		tokens: list[str] = frappe.db.get_all(
			"HiTech Device Token", pluck="token"
		)

		if not tokens:
			frappe.logger().info("[FCM] notify_new_lead: no registered device tokens, skipping.")
			return

		# Initialise Firebase (idempotent across worker processes)
		_get_firebase_app()

		lead_name: str = doc.lead_name or doc.name

		message = messaging.MulticastMessage(
			tokens=tokens,
			notification=messaging.Notification(
				title="New Lead",
				body=f"New lead: {lead_name}",
			),
			data={
				"type": "new_lead",
				"lead": doc.name,
			},
			android=messaging.AndroidConfig(
				notification=messaging.AndroidNotification(
					channel_id="new_leads",
					icon="ic_stat_notify",
				),
			),
		)

		response = messaging.send_each_for_multicast(message)

		frappe.logger().info(
			f"[FCM] notify_new_lead: sent to {len(tokens)} token(s) — "
			f"success={response.success_count}, failure={response.failure_count}"
		)

		# Clean up expired / invalid tokens so they don't accumulate
		_cleanup_invalid_tokens(tokens, response)

	except Exception:
		# Log the full traceback but do NOT re-raise — we must never crash the
		# lead-creation transaction.
		frappe.log_error(
			message=frappe.get_traceback(),
			title="FCM notify_new_lead failed",
		)


def _cleanup_invalid_tokens(tokens: list[str], response) -> None:
	"""Delete tokens whose FCM registration is expired or invalid."""
	from firebase_admin.exceptions import FirebaseError

	invalid_error_codes = {
		"registration-token-not-registered",
		"invalid-registration-token",
		"invalid-argument",
	}

	tokens_to_delete: list[str] = []

	for idx, send_response in enumerate(response.responses):
		if not send_response.success and send_response.exception:
			exc: FirebaseError = send_response.exception
			# firebase-admin surfaces the FCM error code via the http_response
			# attribute or directly on the exception's error_code.
			error_code = getattr(exc, "code", None) or ""
			# Normalise: Firebase may return camelCase or kebab-case strings.
			error_code_normalised = (
				error_code.lower().replace("_", "-")
				if isinstance(error_code, str)
				else ""
			)
			if error_code_normalised in invalid_error_codes:
				tokens_to_delete.append(tokens[idx])

	if tokens_to_delete:
		for token in tokens_to_delete:
			name = frappe.db.get_value("HiTech Device Token", {"token": token}, "name")
			if name:
				frappe.delete_doc("HiTech Device Token", name, ignore_permissions=True)
		frappe.db.commit()
		frappe.logger().info(
			f"[FCM] Cleaned up {len(tokens_to_delete)} invalid/expired token(s)."
		)

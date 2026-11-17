"""Security headers for the public Vue website pages.

Frappe Cloud's proxy already sends HSTS, X-Frame-Options, X-Content-Type-Options and
Referrer-Policy. This adds the two it does not send, only on the pre-rendered Vue pages,
so Desk, the CRM app and the API keep their own behaviour:

- Permissions-Policy: the website uses no camera, microphone, location or payment APIs.
- Content-Security-Policy-Report-Only: a policy that lists every origin the site uses.
  Report-only means browsers log violations in the console but block nothing, so it can be
  checked on the live site before it is switched to an enforcing Content-Security-Policy.
"""

import re

# "/", "/contact", "/privacy", "/about-us", "/cost-guide", "/services/<slug>",
# "/<state>/<district>", with or without a trailing slash.
WEBSITE_PATH = re.compile(
	r"^/(?:|contact|privacy|about-us|cost-guide|services/[a-z0-9-]+|(?:tamil-nadu|karnataka)/[a-z0-9-]+)/?$"
)

PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"

CONTENT_SECURITY_POLICY = "; ".join(
	[
		"default-src 'self'",
		# One small inline script (sets the "js" class) and the pre-rendered critical CSS.
		"script-src 'self' 'unsafe-inline'",
		"style-src 'self' 'unsafe-inline'",
		"img-src 'self' data: blob:",
		"font-src 'self' data:",
		# Enquiry form: Frappe CRM lead API (same origin) and the Web3Forms fallback.
		"connect-src 'self' https://api.web3forms.com",
		"form-action 'self' https://api.web3forms.com",
		"frame-ancestors 'self'",
		"base-uri 'self'",
		"object-src 'none'",
	]
)


def add_website_security_headers(response=None, request=None):
	"""after_request hook: add the headers to HTML responses for the website paths."""
	if response is None or request is None:
		return
	if response.mimetype != "text/html" or not WEBSITE_PATH.match(request.path or ""):
		return
	response.headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
	response.headers.setdefault("Content-Security-Policy-Report-Only", CONTENT_SECURITY_POLICY)

"""Tests for hitech.http_headers (plain unittest; needs only werkzeug)."""

import unittest

from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request, Response

from hitech.http_headers import add_website_security_headers


def run(path, mimetype="text/html"):
	request = Request(EnvironBuilder(path=path).get_environ())
	response = Response("<html></html>", mimetype=mimetype)
	add_website_security_headers(response=response, request=request)
	return response.headers


class TestWebsiteSecurityHeaders(unittest.TestCase):
	def test_website_pages_get_headers(self):
		for path in [
			"/",
			"/contact",
			"/privacy/",
			"/tamil-nadu/salem",
			"/karnataka/bengaluru",
			"/services/well-deepening",
			"/about-us",
			"/cost-guide",
		]:
			with self.subTest(path=path):
				headers = run(path)
				self.assertIn("camera=()", headers["Permissions-Policy"])
				self.assertIn("default-src 'self'", headers["Content-Security-Policy-Report-Only"])
				self.assertNotIn("Content-Security-Policy", headers)

	def test_desk_api_and_crm_untouched(self):
		for path in ["/app", "/app/crm-lead", "/crm", "/crm/leads", "/api/method/ping", "/login", "/me"]:
			with self.subTest(path=path):
				headers = run(path)
				self.assertNotIn("Permissions-Policy", headers)
				self.assertNotIn("Content-Security-Policy-Report-Only", headers)

	def test_non_html_untouched(self):
		headers = run("/", mimetype="application/json")
		self.assertNotIn("Permissions-Policy", headers)

	def test_existing_header_kept(self):
		request = Request(EnvironBuilder(path="/").get_environ())
		response = Response("", mimetype="text/html", headers={"Permissions-Policy": "camera=(self)"})
		add_website_security_headers(response=response, request=request)
		self.assertEqual(response.headers["Permissions-Policy"], "camera=(self)")


if __name__ == "__main__":
	unittest.main()

"""website_redirects in hooks.py, checked with the same matching Frappe uses
(frappe.website.path_resolver.resolve_redirect: source stripped of "/" and " ", "$" appended,
re.match against the path without its leading slash)."""

import re
import unittest

from hitech import hooks


def resolve(path):
	for rule in hooks.website_redirects:
		pattern = rule["source"].strip("/ ") + "$"
		if re.match(pattern, path):
			return re.sub(pattern, rule["target"], path)
	return None


class TestWebsiteRedirects(unittest.TestCase):
	def test_merged_districts(self):
		self.assertEqual(resolve("tamil-nadu/pollachi"), "/tamil-nadu/coimbatore")
		self.assertEqual(resolve("tamil-nadu/rajapalayam"), "/tamil-nadu/virudhunagar")

	def test_old_photo_urls(self):
		self.assertEqual(
			resolve("optimized/hero-1200.e0576965.avif"),
			"/assets/hitech/vue/optimized/hero-1200.e0576965.avif",
		)

	def test_live_pages_not_redirected(self):
		for path in ["", "contact", "tamil-nadu/coimbatore", "tamil-nadu/virudhunagar", "services/well-deepening"]:
			with self.subTest(path=path):
				self.assertIsNone(resolve(path))


if __name__ == "__main__":
	unittest.main()

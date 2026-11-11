"""Serve the packaged Vue site for paths not claimed by Frappe."""

from frappe.website.page_renderers.base_renderer import BaseRenderer
from frappe.website.page_renderers.document_page import DocumentPage
from frappe.website.page_renderers.list_renderer import ListPage
from frappe.website.page_renderers.print_page import PrintPage
from frappe.website.page_renderers.static_page import StaticPage
from frappe.website.page_renderers.template_page import TemplatePage
from frappe.website.page_renderers.web_form import WebFormPage

STANDARD_RENDERERS = (
	StaticPage,
	WebFormPage,
	DocumentPage,
	TemplatePage,
	PrintPage,
	ListPage,
)


class VueFallbackRenderer(BaseRenderer):
	"""Use Vue's index page only when no native Frappe website page matches."""

	def can_render(self):
		return not any(
			renderer(self.path, self.http_status_code).can_render() for renderer in STANDARD_RENDERERS
		)

	def render(self):
		return TemplatePage("index", self.http_status_code).render()

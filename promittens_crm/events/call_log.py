import frappe
from promittens_crm.events.lead import update_lead_status_to_contacted


def on_call_log_after_insert(doc, method=None):
	"""
	Triggered when a CRM Call Log is inserted.
	"""
	_handle_call_log_event(doc, trigger="after_insert")


def on_call_log_update(doc, method=None):
	"""
	Triggered when a CRM Call Log is updated (e.g. linked to a lead).
	"""
	_handle_call_log_event(doc, trigger="on_update")


def _handle_call_log_event(doc, trigger: str):
	try:
		if not doc or doc.doctype != "CRM Call Log":
			return

		lead_names = set()

		# Direct reference
		ref_doctype = getattr(doc, "reference_doctype", None)
		ref_docname = getattr(doc, "reference_docname", None)
		if ref_doctype == "CRM Lead" and ref_docname:
			lead_names.add(ref_docname)

		# Check links child table (Dynamic Link)
		if hasattr(doc, "links") and doc.links:
			for link in doc.links:
				link_doctype = getattr(link, "link_doctype", None)
				link_name = getattr(link, "link_name", None)
				if link_doctype == "CRM Lead" and link_name:
					lead_names.add(link_name)

		for lead_name in lead_names:
			update_lead_status_to_contacted(lead_name, trigger_source=f"Call Log ({trigger})")

	except Exception:
		frappe.log_error(
			title=f"promittens_crm: Error in CRM Call Log hook ({trigger})",
			message=frappe.get_traceback(),
		)

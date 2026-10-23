import frappe
from promittens_crm.events.lead import update_lead_status_to_contacted


def on_communication_after_insert(doc, method=None):
	"""
	Triggered when a Communication document is inserted.
	If an outgoing email is sent for a CRM Lead, change the lead status to Contacted.
	"""
	_handle_communication_event(doc, trigger="after_insert")


def on_communication_update(doc, method=None):
	"""
	Triggered when a Communication document is updated.
	Handles cases where communication sent_or_received is updated to 'Sent'.
	"""
	_handle_communication_event(doc, trigger="on_update")


def _handle_communication_event(doc, trigger: str):
	try:
		if not doc or doc.doctype != "Communication":
			return

		# Must be associated with a CRM Lead
		if doc.reference_doctype != "CRM Lead" or not doc.reference_name:
			return

		# Must be an outgoing communication sent by user/system
		if doc.sent_or_received != "Sent":
			return

		# Medium filter: Email or general Communication
		medium = getattr(doc, "communication_medium", None)
		if medium and medium not in ("Email", "Phone", "Other", ""):
			return

		update_lead_status_to_contacted(doc.reference_name, trigger_source=f"Email ({trigger})")

	except Exception:
		frappe.log_error(
			title=f"promittens_crm: Error in Communication hook ({trigger})",
			message=frappe.get_traceback(),
		)

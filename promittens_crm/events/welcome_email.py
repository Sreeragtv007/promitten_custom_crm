import frappe
from promittens_crm.utils import add_lead_timeline_comment, get_custom_crm_settings


def on_lead_after_insert(doc, method=None):
	"""
	Triggered after a new CRM Lead document is inserted.
	Sends welcome email to the lead's email address if configured in Custom CRM Setting.
	"""
	if not doc:
		return

	if (
		getattr(frappe.flags, "in_import", False)
		or getattr(frappe.flags, "in_patch", False)
		or getattr(frappe.flags, "in_migrate", False)
	):
		return

	if getattr(doc.flags, "skip_welcome_message", False):
		return

	try:
		send_lead_welcome_email_from_settings(doc)
	except Exception:
		frappe.log_error(
			title=f"promittens_crm: Error in lead after_insert hook for CRM Lead {getattr(doc, 'name', '')}",
			message=frappe.get_traceback(),
		)


def send_lead_welcome_email_from_settings(doc) -> bool:
	"""
	Sends welcome email to the lead client based on Custom CRM Setting.

	Returns:
		bool: True if email was queued/sent, False otherwise.
	"""
	settings = get_custom_crm_settings()

	if not settings:
		add_lead_timeline_comment(doc, "Skipped welcome email: Custom CRM Setting not found.")
		return False

	enable_email = bool(getattr(settings, "enable_welcome_email", 0))
	email_subject = (getattr(settings, "welcome_email_subject", None) or "").strip()
	email_message = (getattr(settings, "welcome_email_message", None) or "").strip()

	if not enable_email:
		add_lead_timeline_comment(doc, "Skipped welcome email: Disabled in Custom CRM Setting.")
		return False

	if not email_subject or not email_message:
		add_lead_timeline_comment(doc, "Skipped welcome email: Welcome subject or message is empty in Custom CRM Setting.")
		return False

	email = (getattr(doc, "email", None) or getattr(doc, "email_id", None) or "").strip()
	if not email:
		add_lead_timeline_comment(doc, "Skipped welcome email: No email address provided on lead.")
		return False

	success = send_lead_welcome_email(doc, email, subject=email_subject, message=email_message)
	if success:
		add_lead_timeline_comment(doc, f"Welcome email queued to {email}.")
	return success


def send_lead_welcome_email(doc, recipient_email: str, subject: str, message: str) -> bool:
	"""
	Sends welcome email to the lead client using subject and message from Custom CRM Setting.
	"""
	docname = getattr(doc, "name", "")
	if not subject or not message:
		return False

	try:
		frappe.sendmail(
			recipients=[recipient_email],
			subject=subject,
			message=message,
			reference_doctype="CRM Lead",
			reference_name=docname,
			now=bool(getattr(frappe.flags, "in_test", False)),
		)
		frappe.logger("promittens_crm").info(
			f"Queued welcome email for CRM Lead {docname} to {recipient_email}."
		)
		return True
	except Exception:
		frappe.log_error(
			title=f"promittens_crm: Failed to send welcome email to CRM Lead {docname}",
			message=frappe.get_traceback(),
		)
		return False

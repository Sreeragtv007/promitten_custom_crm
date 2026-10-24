import frappe

TARGET_STATUS = "Contacted"
ELIGIBLE_PREVIOUS_STATUSES = {"New"}


def get_custom_crm_settings():
	"""
	Returns the Custom CRM Setting doc if it exists, or None.
	Uses cached doc for high performance.
	"""
	try:
		if frappe.db.exists("DocType", "Custom CRM Setting"):
			return frappe.get_cached_doc("Custom CRM Setting")
	except Exception:
		pass
	return None


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
	docname = getattr(doc, "name", "")
	settings = get_custom_crm_settings()

	if not settings:
		add_lead_timeline_comment(doc, f"Skipped welcome email: Custom CRM Setting not found.")
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


def add_lead_timeline_comment(doc, text: str):
	"""
	Safely adds an informational comment to the Lead's timeline in Desk.
	Never raises an error and ignores bulk data imports.
	"""
	try:
		if doc and hasattr(doc, "add_comment") and not getattr(frappe.flags, "in_import", False):
			doc.add_comment("Info", text)
	except Exception:
		pass


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


def update_lead_status_to_contacted(lead_name: str, trigger_source: str = "activity") -> bool:
	"""
	Safely updates a CRM Lead status to 'Contacted' if it is in an initial eligible status.

	Args:
		lead_name: The name/ID of the CRM Lead.
		trigger_source: Descriptive source (e.g. 'Email', 'Call Log') for logging.

	Returns:
		bool: True if status was changed, False otherwise.
	"""
	if not lead_name or not isinstance(lead_name, str):
		return False

	try:
		if not frappe.db.exists("CRM Lead", lead_name):
			return False

		# Ensure target status exists in the system
		if not frappe.db.exists("CRM Lead Status", TARGET_STATUS):
			frappe.logger("promittens_crm").warning(
				f"Cannot update CRM Lead {lead_name}: Status '{TARGET_STATUS}' does not exist in CRM Lead Status."
			)
			return False

		current_status = frappe.db.get_value("CRM Lead", lead_name, "status")
		if not current_status:
			current_status = "New"

		# If already Contacted or not eligible (e.g., Qualified, Converted, Lost, Junk), do nothing
		if current_status == TARGET_STATUS or current_status not in ELIGIBLE_PREVIOUS_STATUSES:
			return False

		lead_doc = frappe.get_doc("CRM Lead", lead_name)

		# Double-check against latest fetched document
		if lead_doc.status != TARGET_STATUS and (lead_doc.status in ELIGIBLE_PREVIOUS_STATUSES or not lead_doc.status):
			lead_doc.status = TARGET_STATUS
			try:
				lead_doc.save(ignore_permissions=True)
			except Exception as save_err:
				frappe.logger("promittens_crm").warning(
					f"lead.save() failed for CRM Lead {lead_name} ({save_err}). Falling back to db_set."
				)
				lead_doc.db_set("status", TARGET_STATUS)

			return True

	except Exception:
		frappe.log_error(
			title=f"promittens_crm: Failed to update CRM Lead {lead_name} status via {trigger_source}",
			message=frappe.get_traceback(),
		)
		return False

	return False

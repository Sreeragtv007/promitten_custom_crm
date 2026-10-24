import frappe

TARGET_STATUS = "Contacted"
ELIGIBLE_PREVIOUS_STATUSES = {"New"}


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

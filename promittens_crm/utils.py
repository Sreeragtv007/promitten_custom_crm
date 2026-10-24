import frappe


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


def add_lead_timeline_comment(doc, text: str):
	"""
	Safely adds a comment to the Lead's timeline in Frappe CRM.
	Uses comment_type='Comment' so it renders in both the Activity timeline
	and the dedicated Comments tab.
	Never raises an error and ignores bulk data imports.
	"""
	try:
		if doc and hasattr(doc, "add_comment") and not getattr(frappe.flags, "in_import", False):
			doc.add_comment("Comment", text)
	except Exception:
		frappe.logger("promittens_crm").warning(
			f"Failed to add timeline comment to Lead {getattr(doc, 'name', '')}: {text}"
		)

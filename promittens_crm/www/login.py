# Copyright (c) 2026, Promittens and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.www.login import get_context as get_frappe_login_context

no_cache = True


def get_context(context):
	# Inherit native Frappe login context (redirects, providers, security settings)
	context = get_frappe_login_context(context)

	context["brand_name"] = "Promittens CRM"
	context["app_name"] = "Promittens CRM"
	context["title"] = "Promittens CRM - Login"

	# If default logo is Frappe framework icon, unset it so custom clean branding is used
	logo_val = str(context.get("logo") or "")
	if "frappe" in logo_val.lower():
		context["logo"] = None

	return context

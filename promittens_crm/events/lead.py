"""
Module: promittens_crm.events.lead
Maintains backward compatibility by re-exporting lead event handlers and status automation.
Feature logic is organized into:
- promittens_crm.events.welcome_email: Lead welcome email automation
- promittens_crm.events.lead_status: CRM Lead status transitions
- promittens_crm.utils: Shared CRM utility functions
"""

from promittens_crm.utils import (
	add_lead_timeline_comment,
	get_custom_crm_settings,
)
from promittens_crm.events.welcome_email import (
	on_lead_after_insert,
	send_lead_welcome_email,
	send_lead_welcome_email_from_settings,
)
from promittens_crm.events.lead_status import (
	ELIGIBLE_PREVIOUS_STATUSES,
	TARGET_STATUS,
	update_lead_status_to_contacted,
)

__all__ = [
	"get_custom_crm_settings",
	"add_lead_timeline_comment",
	"on_lead_after_insert",
	"send_lead_welcome_email_from_settings",
	"send_lead_welcome_email",
	"TARGET_STATUS",
	"ELIGIBLE_PREVIOUS_STATUSES",
	"update_lead_status_to_contacted",
]

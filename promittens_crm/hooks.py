app_name = "promittens_crm"
app_title = "Promittens Crm"
app_publisher = "sreerag"
app_description = "custom crm"
app_email = "sreeragtv009@gmail.com"
app_license = "mit"

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Communication": {
		"after_insert": "promittens_crm.events.communication.on_communication_after_insert",
		"on_update": "promittens_crm.events.communication.on_communication_update",
	},
	"CRM Call Log": {
		"after_insert": "promittens_crm.events.call_log.on_call_log_after_insert",
		"on_update": "promittens_crm.events.call_log.on_call_log_update",
	},
}

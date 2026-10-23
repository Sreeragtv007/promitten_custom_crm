import unittest
import frappe


class TestLeadStatusAutomation(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# Ensure default statuses exist
		if not frappe.db.exists("CRM Lead Status", "New"):
			frappe.get_doc({"doctype": "CRM Lead Status", "lead_status": "New", "type": "Open"}).insert()
		if not frappe.db.exists("CRM Lead Status", "Contacted"):
			frappe.get_doc({"doctype": "CRM Lead Status", "lead_status": "Contacted", "type": "Ongoing"}).insert()
		if not frappe.db.exists("CRM Lead Status", "Qualified"):
			frappe.get_doc({"doctype": "CRM Lead Status", "lead_status": "Qualified", "type": "Won"}).insert()

	def create_lead(self, status="New"):
		lead = frappe.new_doc("CRM Lead")
		lead.first_name = "Test"
		lead.last_name = f"Lead_{frappe.generate_hash(length=6)}"
		lead.email = f"lead_{frappe.generate_hash(length=6)}@example.com"
		lead.status = status
		lead.insert(ignore_permissions=True)
		return lead

	def test_email_changes_new_lead_to_contacted(self):
		lead = self.create_lead(status="New")
		self.assertEqual(lead.status, "New")

		comm = frappe.new_doc("Communication")
		comm.communication_type = "Communication"
		comm.communication_medium = "Email"
		comm.sent_or_received = "Sent"
		comm.reference_doctype = "CRM Lead"
		comm.reference_name = lead.name
		comm.subject = "Follow up test email"
		comm.content = "Hello, following up with you."
		comm.sender = "admin@example.com"
		comm.recipients = lead.email
		comm.insert(ignore_permissions=True)

		lead.reload()
		self.assertEqual(lead.status, "Contacted")
		# Verify CRM Status Change Log was updated
		self.assertTrue(any(log.to == "Contacted" for log in lead.status_change_log))

	def test_call_log_changes_new_lead_to_contacted(self):
		lead = self.create_lead(status="New")
		self.assertEqual(lead.status, "New")

		call_log = frappe.new_doc("CRM Call Log")
		call_log.set("from", "1234567890")
		call_log.to = "9876543210"
		call_log.type = "Outgoing"
		call_log.status = "Completed"
		call_log.reference_doctype = "CRM Lead"
		call_log.reference_docname = lead.name
		call_log.insert(ignore_permissions=True)

		lead.reload()
		self.assertEqual(lead.status, "Contacted")
		# Verify CRM Status Change Log was updated
		self.assertTrue(any(log.to == "Contacted" for log in lead.status_change_log))

	def test_call_log_links_child_table_changes_status(self):
		lead = self.create_lead(status="New")
		self.assertEqual(lead.status, "New")

		call_log = frappe.new_doc("CRM Call Log")
		call_log.set("from", "1234567890")
		call_log.to = "9876543210"
		call_log.type = "Outgoing"
		call_log.status = "Completed"
		call_log.append("links", {"link_doctype": "CRM Lead", "link_name": lead.name})
		call_log.insert(ignore_permissions=True)

		lead.reload()
		self.assertEqual(lead.status, "Contacted")
		# Verify CRM Status Change Log was updated
		self.assertTrue(any(log.to == "Contacted" for log in lead.status_change_log))

	def test_qualified_lead_is_not_reverted_to_contacted(self):
		lead = self.create_lead(status="Qualified")
		self.assertEqual(lead.status, "Qualified")

		# Send an email
		comm = frappe.new_doc("Communication")
		comm.communication_type = "Communication"
		comm.communication_medium = "Email"
		comm.sent_or_received = "Sent"
		comm.reference_doctype = "CRM Lead"
		comm.reference_name = lead.name
		comm.subject = "Qualified lead check"
		comm.sender = "admin@example.com"
		comm.insert(ignore_permissions=True)

		lead.reload()
		self.assertEqual(lead.status, "Qualified")

	def test_incoming_email_does_not_change_status(self):
		lead = self.create_lead(status="New")
		self.assertEqual(lead.status, "New")

		# Received email (not sent by agent)
		comm = frappe.new_doc("Communication")
		comm.communication_type = "Communication"
		comm.communication_medium = "Email"
		comm.sent_or_received = "Received"
		comm.reference_doctype = "CRM Lead"
		comm.reference_name = lead.name
		comm.subject = "Inbound inquiry"
		comm.sender = lead.email
		comm.insert(ignore_permissions=True)

		lead.reload()
		self.assertEqual(lead.status, "New")

import unittest
from unittest.mock import patch
import frappe

TEST_WELCOME_SUBJECT = "Thank you for contacting us"
TEST_WELCOME_MESSAGE = (
	"Thank you for contacting us. We are looking forward to work with you. "
	"We will contact you for more details as soon as possible"
)


class TestLeadWelcomeEmail(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# Ensure default statuses exist
		if not frappe.db.exists("CRM Lead Status", "New"):
			frappe.get_doc({"doctype": "CRM Lead Status", "lead_status": "New", "type": "Open"}).insert()

		# Ensure Custom CRM Setting has active email configuration
		if frappe.db.exists("DocType", "Custom CRM Setting"):
			settings = frappe.get_doc("Custom CRM Setting")
			settings.enable_welcome_email = 1
			settings.welcome_email_subject = TEST_WELCOME_SUBJECT
			settings.welcome_email_message = TEST_WELCOME_MESSAGE
			settings.save(ignore_permissions=True)
			frappe.clear_cache(doctype="Custom CRM Setting")

	def create_lead(self, email=None, flags=None):
		lead = frappe.new_doc("CRM Lead")
		lead.first_name = "Jane"
		lead.last_name = f"Doe_{frappe.generate_hash(length=6)}"
		if email:
			lead.email = email
		lead.status = "New"
		if flags:
			for k, v in flags.items():
				lead.flags[k] = v
		lead.insert(ignore_permissions=True)
		return lead

	def test_lead_created_with_email_sends_welcome_email(self):
		"""
		Tests that welcome email is triggered with subject and message from Custom CRM Setting.
		"""
		test_email = f"lead_{frappe.generate_hash(length=6)}@example.com"

		with patch("frappe.sendmail") as mock_sendmail:
			lead = self.create_lead(email=test_email)

			mock_sendmail.assert_called_once()
			_, sendmail_kwargs = mock_sendmail.call_args
			self.assertEqual(sendmail_kwargs.get("recipients"), [test_email])
			self.assertEqual(sendmail_kwargs.get("subject"), TEST_WELCOME_SUBJECT)
			self.assertEqual(sendmail_kwargs.get("message"), TEST_WELCOME_MESSAGE)
			self.assertEqual(sendmail_kwargs.get("reference_doctype"), "CRM Lead")
			self.assertEqual(sendmail_kwargs.get("reference_name"), lead.name)

			# Verify initial status stays New
			lead.reload()
			self.assertEqual(lead.status, "New")

	def test_custom_crm_setting_custom_subject_and_message(self):
		"""
		Tests that Custom CRM Setting custom subject and message are dynamically fetched and sent.
		"""
		test_email = f"lead_custom_{frappe.generate_hash(length=6)}@example.com"
		custom_subject = "Welcome aboard from Promittens!"
		custom_message = "Hello! We received your request and will follow up shortly."

		settings = frappe.get_doc("Custom CRM Setting")
		settings.welcome_email_subject = custom_subject
		settings.welcome_email_message = custom_message
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="Custom CRM Setting")

		with patch("frappe.sendmail") as mock_sendmail:
			lead = self.create_lead(email=test_email)

			mock_sendmail.assert_called_once()
			_, sendmail_kwargs = mock_sendmail.call_args
			self.assertEqual(sendmail_kwargs.get("subject"), custom_subject)
			self.assertEqual(sendmail_kwargs.get("message"), custom_message)

	def test_custom_crm_setting_disables_email(self):
		"""
		Tests that unchecking enable_welcome_email in Custom CRM Setting suppresses emails.
		"""
		test_email = f"lead_disabled_{frappe.generate_hash(length=6)}@example.com"

		settings = frappe.get_doc("Custom CRM Setting")
		settings.enable_welcome_email = 0
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="Custom CRM Setting")

		with patch("frappe.sendmail") as mock_sendmail:
			lead = self.create_lead(email=test_email)
			mock_sendmail.assert_not_called()

	def test_empty_subject_or_message_skips_email(self):
		"""
		Tests that if subject or message is empty in Custom CRM Setting, email is safely skipped.
		"""
		test_email = f"lead_empty_{frappe.generate_hash(length=6)}@example.com"

		settings = frappe.get_doc("Custom CRM Setting")
		settings.welcome_email_subject = ""
		settings.welcome_email_message = ""
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="Custom CRM Setting")

		with patch("frappe.sendmail") as mock_sendmail:
			lead = self.create_lead(email=test_email)
			mock_sendmail.assert_not_called()

	def test_lead_without_email_skips_cleanly(self):
		"""
		Tests that creating a lead without email succeeds smoothly without errors.
		"""
		with patch("frappe.sendmail") as mock_sendmail:
			lead = self.create_lead()
			self.assertTrue(lead.name)
			mock_sendmail.assert_not_called()

	def test_email_error_does_not_abort_lead_creation(self):
		"""
		Tests that SMTP/mail errors are caught, logged, and do not break lead creation.
		"""
		test_email = f"lead_fail_{frappe.generate_hash(length=6)}@example.com"

		with patch("frappe.sendmail", side_effect=Exception("SMTP Connection Error")), patch(
			"frappe.log_error"
		) as mock_log_error:
			lead = self.create_lead(email=test_email)
			self.assertTrue(lead.name)
			self.assertTrue(frappe.db.exists("CRM Lead", lead.name))
			mock_log_error.assert_called()

	def test_skip_welcome_message_flag(self):
		"""
		Tests that setting doc.flags.skip_welcome_message suppresses email.
		"""
		test_email = f"lead_skip_{frappe.generate_hash(length=6)}@example.com"

		with patch("frappe.sendmail") as mock_sendmail:
			lead = self.create_lead(email=test_email, flags={"skip_welcome_message": True})
			mock_sendmail.assert_not_called()

	def test_import_flag_suppresses_welcome_email(self):
		"""
		Tests that frappe.flags.in_import suppresses welcome email.
		"""
		test_email = f"lead_import_{frappe.generate_hash(length=6)}@example.com"

		frappe.flags.in_import = True
		try:
			with patch("frappe.sendmail") as mock_sendmail:
				lead = self.create_lead(email=test_email)
				mock_sendmail.assert_not_called()
		finally:
			frappe.flags.in_import = False

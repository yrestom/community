# -*- coding: utf-8 -*-
# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json
from frappe.utils.password import get_decrypted_password

class InviteRequest(Document):
	def on_update(self):
		if self.has_value_changed('status') and self.status == "Approved":
			self.send_email()

	def create_user(self, password):
		user = 	frappe.get_doc({
					"doctype": "User",
					"email": self.signup_email,
					"first_name": self.full_name.split(" ")[0],
					"full_name": self.full_name,
					"username": self.username,
					"send_welcome_email": 0,
					"user_type": 'Website User',
					"new_password": password
				})
		user.save(ignore_permissions=True)
		return user

	def send_email(self):
		subject = _("Your request has been approved.")
		args = {
			"full_name": self.full_name,
			"signup_form_link": "/new-sign-up?invite_code={0}".format(self.name),
			"site_url": frappe.utils.get_url()
		}
		frappe.sendmail(
			recipients=self.invite_email,
			sender=frappe.db.get_single_value("LMS Settings", "email_sender"),
			subject=subject,
			header=[subject, "green"],
			template = "lms_invite_request_approved",
			args=args)

@frappe.whitelist(allow_guest=True)
def create_invite_request(email):
	frappe.get_doc({
		"doctype": "Invite Request",
		"invite_email": email
	}).save(ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def update_invite(data):
	data = frappe._dict(json.loads(data))

	try:
		doc = frappe.get_doc("Invite Request", data.invite_code)
	except frappe.DoesNotExistError:
		frappe.throw(_("Invalid Invite Code."))

	doc.signup_email = data.signup_email
	doc.username = data.username
	doc.full_name = data.full_name
	doc.invite_code = data.invite_code
	doc.save(ignore_permissions=True)

	user = doc.create_user(data.password)
	if user:
		doc.status = "Registered"
		doc.save(ignore_permissions=True)

	return "OK"
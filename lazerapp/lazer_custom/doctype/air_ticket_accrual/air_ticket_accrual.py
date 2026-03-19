# Copyright (c) 2026, eldho.mathew@webtreeonline.com and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from frappe.utils import today, flt, getdate

class AirTicketAccrual(Document):

    def before_save(self):
        calculate_air_ticket(self)

def calculate_air_ticket(doc, method=None):

    if not doc.rejoining_date or not doc.maximum_ticket_amount:
        return

    total_months = 24

    doc.yearly_amount = flt(doc.maximum_ticket_amount) / 2
    doc.monthly_accrual = flt(doc.maximum_ticket_amount) / total_months

    today_date = getdate(today())
    rejoin_date = getdate(doc.rejoining_date)

    months_completed = (
        (today_date.year - rejoin_date.year) * 12
        + today_date.month
        - rejoin_date.month
    )

    months_completed = months_completed % total_months
    doc.months_completed = max(0, months_completed)

    accrued = doc.monthly_accrual * doc.months_completed
    doc.available_balance = accrued

    # ✅ ONLY FIRST TIME SET
    if doc.is_new():
        used_amount = flt(doc.used_amount)
        doc.loan_amount = used_amount - accrued if used_amount > accrued else 0

    doc.last_calculated_on = today()


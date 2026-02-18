# Copyright (c) 2026, eldho.mathew@webtreeonline.com and contributors
# For license information, please see license.txt
from frappe.model.document import Document
from frappe.utils import today, date_diff


class AirTicketAccrual(Document):

    def before_save(self):
        calculate_air_ticket(self)


def calculate_air_ticket(doc):

    if not doc.rejoining_date or not doc.max_ticket_amount:
        return

    # 2 Year Logic
    total_months = 24

    # Yearly Amount
    doc.yearly_amount = doc.max_ticket_amount / 2

    # Monthly Accrual
    doc.monthly_accrual = doc.max_ticket_amount / total_months

    # Months completed from rejoining date
    months_completed = date_diff(today(), doc.rejoining_date) // 30
    doc.months_completed = max(0, months_completed)

    # If more than 24 months → reset
    if doc.months_completed > 24:
        doc.available_balance = 0
        return

    # Available Balance
    doc.available_balance = doc.monthly_accrual * doc.months_completed

    # Loan calculation
    if doc.used_amount and doc.used_amount > doc.available_balance:
        doc.loan_amount = doc.used_amount - doc.available_balance
    else:
        doc.loan_amount = 0



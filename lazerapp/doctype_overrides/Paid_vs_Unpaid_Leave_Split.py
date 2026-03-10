import frappe
from frappe.utils import flt

def validate(doc, method=None):
    

    leave_balance = flt(doc.leave_balance or 0)
    total_days = flt(doc.total_leave_days or 0)

    if total_days <= 0:
        frappe.throw("Total Leave Days must be greater than 0")

    doc.paid_leave_days = min(total_days, leave_balance)
    doc.unpaid_leave_days = max(total_days - leave_balance, 0)

    if total_days > leave_balance:
        doc.flags.ignore_leave_balance = True

    frappe.msgprint(
        f"Paid Leave: {doc.paid_leave_days} | Unpaid Leave: {doc.unpaid_leave_days}"
    )
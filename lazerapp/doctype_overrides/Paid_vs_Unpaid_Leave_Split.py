import frappe
from frappe.utils import flt
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on


def validate(doc, method=None):

    leave_balance = flt(get_leave_balance_on(
        doc.employee,
        doc.leave_type,
        doc.from_date
    ))

    total_days = flt(doc.total_leave_days)

    doc.custom_paid_leave_days = min(total_days, leave_balance)
    doc.custom_unpaid_leave_days = max(total_days - leave_balance, 0)

    if doc.custom_unpaid_leave_days > 0:
<<<<<<< HEAD
        doc.flags.ignore_leave_balance = True
=======
        doc.flags.ignore_leave_balance = True

>>>>>>> 19ae3bb9c82fb01e2c0188c42fcd6392b1a4bcf3

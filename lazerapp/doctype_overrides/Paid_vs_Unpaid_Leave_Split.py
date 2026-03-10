import frappe
<<<<<<< HEAD
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
=======

def validate(self):
    leave_balance = frappe.db.get_value(
        "Leave Allocation",
        {"employee": self.employee, "leave_type": self.leave_type},
        "total_leaves_allocated"
    ) or 0

    if self.total_leave_days > leave_balance:
        self.paid_leave_days = leave_balance
        self.unpaid_leave_days = self.total_leave_days - leave_balance
    else:
        self.paid_leave_days = self.total_leave_days
        self.unpaid_leave_days = 0
>>>>>>> 9254072939bef416aed5853d21e1352144f8f7fc

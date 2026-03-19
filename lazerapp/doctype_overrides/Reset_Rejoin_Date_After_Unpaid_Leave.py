import frappe
from frappe.utils import add_days

def on_submit(doc, method):
    if doc.custom_unpaid_leave_days and doc.custom_unpaid_leave_days > 0:
        frappe.db.set_value(
            "Employee",
            doc.employee,
            "custom_rejoin_date",
            add_days(doc.to_date, 1)  # Next day rejoining
        )

import frappe

def on_submit(self):
    if self.unpaid_leave_days and self.unpaid_leave_days > 0:
        frappe.db.set_value(
            "Employee",
            self.employee,
            "rejoin_date",
            self.to_date
        )

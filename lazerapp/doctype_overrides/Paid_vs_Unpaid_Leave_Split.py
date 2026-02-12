import frappe

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

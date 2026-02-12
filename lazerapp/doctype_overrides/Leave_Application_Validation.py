import frappe

def validate(self):
    nationality = frappe.db.get_value(
        "Employee",
        self.employee,
        "nationality"
    )

    if nationality != "Bahraini" and self.leave_type != "Annual Leave":
        frappe.throw("Only Annual Leave is allowed for non-Bahraini employees")

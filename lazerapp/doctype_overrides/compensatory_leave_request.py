import frappe

def validate(doc, method):
    if doc.leave_type != "Compensatory Leave":
        return

    if not doc.employee:
        return

    employee = frappe.get_doc("Employee", doc.employee)

    branch = (employee.branch or "").strip().lower()

    if branch != "head office":
        frappe.throw(
            "Only Head Office employees can apply Compensatory Leave."
        )

import frappe

def update_all_employee_air_ticket():
    docs = frappe.get_all("Air Ticket Accrual", pluck="name")

    for d in docs:
        doc = frappe.get_doc("Air Ticket Accrual", d)
        doc.save(ignore_permissions=True)

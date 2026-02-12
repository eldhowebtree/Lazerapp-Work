import frappe
from frappe.utils import getdate, nowdate

def process_leave_encashment():
    allocations = frappe.get_all(
        "Leave Allocation",
        filters={"leave_type": "Annual Leave"},
        fields=["name", "employee", "from_date", "total_leaves_allocated"]
    )

    today = getdate(nowdate())

    for alloc in allocations:
        from_date = getdate(alloc.from_date)
        years_passed = today.year - from_date.year

        if years_passed > 2 and alloc.total_leaves_allocated > 0:
            basic_salary = frappe.db.get_value(
                "Salary Structure Assignment",
                {"employee": alloc.employee},
                "base"
            ) or 0

            encash_amount = (basic_salary / 30) * alloc.total_leaves_allocated

            frappe.db.set_value(
                "Leave Allocation",
                alloc.name,
                "total_leaves_allocated",
                0
            )

import frappe
from frappe.utils import getdate, nowdate

def credit_monthly_annual_leave():
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "date_of_joining", "rejoin_date"]
    )

    today = getdate(nowdate())

    for emp in employees:
        start_date = emp.rejoin_date or emp.date_of_joining
        if not start_date:
            continue

        start_date = getdate(start_date)
        months_completed = (today.year - start_date.year) * 12 + (today.month - start_date.month)

        if months_completed <= 0:
            continue

        allocation = frappe.db.get_value(
            "Leave Allocation",
            {"employee": emp.name, "leave_type": "Annual Leave"},
            ["name", "total_leaves_allocated"],
            as_dict=True
        )

        if not allocation:
            continue

        new_balance = min(months_completed * 2.5, 30)

        frappe.db.set_value(
            "Leave Allocation",
            allocation.name,
            "total_leaves_allocated",
            new_balance
        )

import frappe

def calculate_leave_salary(employee):
    basic_salary = frappe.db.get_value(
        "Salary Structure Assignment",
        {"employee": employee},
        "base"
    ) or 0

    leave_balance = frappe.db.get_value(
        "Leave Allocation",
        {"employee": employee, "leave_type": "Annual Leave"},
        "total_leaves_allocated"
    ) or 0

    one_day_salary = basic_salary / 30
    return leave_balance * one_day_salary

import frappe
from frappe.utils import getdate, nowdate, date_diff


def check_vacation_overstay():
    """
    Daily job:
    - Check approved Annual/Vacation leave
    - If employee did not rejoin after expected date
    - Send mail to HR Manager + System Manager + Employee
    """

    today = getdate(nowdate())

    VACATION_LEAVE_TYPES = ["Annual Leave", "Vacation Leave"]

    leaves = frappe.get_all(
        "Leave Application",
        filters={
            "status": "Approved",
            "leave_type": ["in", VACATION_LEAVE_TYPES],
            "custom_expected_rejoin_date": ["<", today]
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "from_date",
            "to_date",
            "custom_expected_rejoin_date"
        ]
    )

    if not leaves:
        return

    hr_users = frappe.get_all(
        "Has Role",
        filters={"role": ["in", ["HR Manager", "Branch Admin"]]},
        pluck="parent"
    )

    for leave in leaves:
        emp_status = frappe.db.get_value(
            "Employee", leave.employee, "status"
        )
        if emp_status != "Active":
            continue

        expected_rejoin = getdate(leave.custom_expected_rejoin_date)
        days_overstay = date_diff(today, expected_rejoin)

        employee_user = frappe.db.get_value(
            "Employee", leave.employee, "user_id"
        )

        recipients = list(set(hr_users))
        if employee_user:
            recipients.append(employee_user)

        subject = f"Vacation Overstay Alert – {leave.employee_name}"

        message = f"""
        <p><b>Vacation Overstay Detected</b></p>
        <p>
        Employee <b>{leave.employee_name}</b> ({leave.employee})
        has not rejoined after vacation.
        </p>
        <p>
        <b>Leave Period:</b><br>
        From: {leave.from_date}<br>
        To: {leave.to_date}
        </p>
        <p>
        <b>Expected Rejoin Date:</b> {expected_rejoin}<br>
        <b>Overstay:</b> {days_overstay} day(s)
        </p>
        """

        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            delayed=False
        )

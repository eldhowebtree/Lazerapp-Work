import frappe
from frappe.utils import getdate, nowdate, date_diff
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication


class CustomLeaveApplication(LeaveApplication):

    def on_update(self):
        """
        Trigger overstay check whenever leave is updated
        """
        self.check_vacation_overstay()

    @staticmethod
    def check_vacation_overstay():
        """
        Detect employees who did not rejoin after vacation
        """
        today = getdate(nowdate())

        VACATION_LEAVE_TYPES = [
            "Annual Leave",
            "Vacation Leave"
        ]

        leaves = frappe.get_all(
            "Leave Application",
            filters={
                "status": "Approved",
                "leave_type": ["in", VACATION_LEAVE_TYPES],
                "custom_expected_rejoin_date": ["is", "set"]
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

        for leave in leaves:
            expected_rejoin = getdate(leave.custom_expected_rejoin_date)

            if expected_rejoin >= today:
                continue

            emp_status = frappe.db.get_value(
                "Employee", leave.employee, "status"
            )

            if emp_status != "Active":
                continue

            days_overstay = date_diff(today, expected_rejoin)

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
                recipients=frappe.get_all(
                    "Has Role",
                    filters={
                        "role": ["in", ["HR Manager", "System Manager"]]
                    },
                    pluck="parent"
                ),
                subject=subject,
                message=message
            )

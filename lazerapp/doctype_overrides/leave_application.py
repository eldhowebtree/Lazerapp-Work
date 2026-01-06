from hrms.hr.doctype.leave_application.leave_application import LeaveApplication


class CustomLeaveApplication(LeaveApplication):
    """
    Leave Application override.
    Overstay is handled by scheduler, not here.
    """
    pass

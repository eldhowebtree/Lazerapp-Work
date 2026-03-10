import frappe
from datetime import datetime

def calculate_employee_indemnity(doc, method):
    """Auto calculate indemnity and total years of service before saving Employee Transfer"""

    # Validate required fields
    if not doc.custom_basic_salary_take_home or not doc.custom_date_of_joining or not doc.transfer_date:
        doc.custom_total_years_of_service = 0
        doc.custom_indemnity_type = ""
        doc.custom_calculated_indemnity = 0
        return

    # Convert string dates to datetime
    salary = float(doc.custom_basic_salary_take_home)
    doj = datetime.strptime(str(doc.custom_date_of_joining), "%Y-%m-%d")
    dot = datetime.strptime(str(doc.transfer_date), "%Y-%m-%d")

    # Calculate total service years
    years = max(0, (dot - doj).days // 365)
    doc.custom_total_years_of_service = years

    # Calculate indemnity based on service duration
    if years <= 3:
        indemnity = (salary / 30) * 15 * years
        doc.custom_indemnity_type = "15 Days Salary / Year"
    else:
        indemnity = salary * years
        doc.custom_indemnity_type = "1 Month Salary / Year"

    doc.custom_calculated_indemnity = indemnity

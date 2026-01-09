import frappe
from frappe import _
from frappe.utils import flt, getdate, get_last_day, date_diff
from datetime import datetime, timedelta
import calendar

@frappe.whitelist()
def calculate_monthly_overtime(employee, month, year):
    """
    Calculate overtime for an employee for entire month based on their category
    """
    month = int(month)
    year = int(year)

    # Get month start and end dates
    start_date = getdate(f"{year}-{month:02d}-01")
    end_date = get_last_day(start_date)
    days_in_month = calendar.monthrange(year, month)[1]
    
    # Get employee details
    employee_doc = frappe.get_doc("Employee", employee)
    ot_category = employee_doc.get('ot_category')
    
    if not ot_category:
        frappe.throw(_("Please set OT Category for employee {0}").format(employee_doc.employee_name))
    
    # Get salary details
    salary_assignment = frappe.get_value(
        "Salary Structure Assignment",
        {
            "employee": employee,
            "docstatus": 1,
            "from_date": ["<=", end_date]
        },
        ["base", "gross_salary"],
        as_dict=1,
        order_by="from_date desc"
    )
    
    if not salary_assignment:
        frappe.throw(_("No active salary structure found for employee {0}").format(employee_doc.employee_name))
    
    base_salary = flt(salary_assignment.base)
    gross_salary = flt(salary_assignment.gross_salary) or base_salary
    
    # Get all attendance for the month
    attendance_list = frappe.get_all("Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [start_date, end_date]],
            "status": "Present",
            "docstatus": 1
        },
        fields=["name", "attendance_date", "working_hours", "is_public_holiday"]
    )
    
    # Calculate total working hours
    total_working_hours = sum([flt(att.working_hours, 2) for att in attendance_list])
    
    # Calculate based on category
    if ot_category == "Category 1 - Cleaners & Serviceman":
        result = calculate_category_1(employee_doc, gross_salary, total_working_hours, 
                                       attendance_list, days_in_month)
    
    elif ot_category == "Category 2 - Lazer VTC":
        result = calculate_category_2(employee_doc, base_salary, total_working_hours, 
                                       attendance_list, days_in_month)
    
    elif ot_category == "Category 3 - Admins (Branch Office)":
        result = calculate_category_3(employee_doc, base_salary, total_working_hours, 
                                       attendance_list, days_in_month)
    
    elif ot_category == "Category 4 - Head Office":
        result = calculate_category_4(employee_doc, base_salary, total_working_hours, 
                                       attendance_list, days_in_month, start_date, end_date)
    else:
        frappe.throw(_("Invalid OT Category"))
    
    # Update attendance records with OT details
    update_attendance_records(attendance_list, result)
    
    return result


def calculate_category_1(employee, gross_salary, total_hours, attendance_list, days_in_month):
    """
    Category 1: Cleaners & Serviceman
    Mandatory: 10 hours/day
    Formula: (Gross Salary / 30) / 10 * Extra Hours
    """
    mandatory_hours_per_day = 10
    working_days = len(attendance_list)
    
    # Calculate working days (26 or 27 based on month)
    if days_in_month == 31:
        expected_working_days = 27
    else:
        expected_working_days = 26
    
    mandatory_hours_per_month = mandatory_hours_per_day * expected_working_days
    extra_hours = max(0, total_hours - mandatory_hours_per_month)
    
    # Calculation
    daily_rate = gross_salary / 30
    hourly_rate = daily_rate / mandatory_hours_per_day
    overtime_amount = hourly_rate * extra_hours
    
    return {
        "category": "Category 1 - Cleaners & Serviceman",
        "gross_salary": gross_salary,
        "total_working_hours": total_hours,
        "mandatory_hours": mandatory_hours_per_month,
        "extra_hours": extra_hours,
        "hourly_rate": hourly_rate,
        "overtime_amount": overtime_amount,
        "calculation_breakdown": {
            "daily_rate": daily_rate,
            "hourly_rate": hourly_rate,
            "formula": f"{gross_salary}/30 = {daily_rate:.3f}, {daily_rate:.3f}/10 = {hourly_rate:.3f}, {hourly_rate:.3f} * {extra_hours} = {overtime_amount:.3f}"
        }
    }


def calculate_category_2(employee, base_salary, total_hours, attendance_list, days_in_month):
    """
    Category 2: Lazer VTC
    Mandatory: 8 hours/day
    Normal Day: Extra hours * 1.25
    Public Holiday: Hours * 1.5
    """
    mandatory_hours_per_day = 8
    
    # Calculate working days (26 or 27)
    if days_in_month == 31:
        expected_working_days = 27
    else:
        expected_working_days = 26
    
    mandatory_hours_per_month = mandatory_hours_per_day * expected_working_days
    
    # Separate public holiday and normal day hours
    public_holiday_hours = sum([flt(att.working_hours, 2) for att in attendance_list if att.is_public_holiday])
    normal_day_hours = total_hours - public_holiday_hours
    
    # Calculate extra hours on normal days
    extra_normal_hours = max(0, normal_day_hours - mandatory_hours_per_month)
    
    # Calculate OT
    normal_day_ot = extra_normal_hours * 1.25
    public_holiday_ot = public_holiday_hours * 1.5
    total_ot_amount = normal_day_ot + public_holiday_ot
    
    return {
        "category": "Category 2 - Lazer VTC",
        "base_salary": base_salary,
        "total_working_hours": total_hours,
        "mandatory_hours": mandatory_hours_per_month,
        "normal_day_hours": normal_day_hours,
        "extra_normal_hours": extra_normal_hours,
        "public_holiday_hours": public_holiday_hours,
        "normal_day_ot": normal_day_ot,
        "public_holiday_ot": public_holiday_ot,
        "overtime_amount": total_ot_amount,
        "calculation_breakdown": {
            "normal_formula": f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
            "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
            "total": f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
        }
    }


def calculate_category_3(employee, base_salary, total_hours, attendance_list, days_in_month):
    """
    Category 3: Admins (Branch Office)
    Mandatory: 10 hours/day
    Normal Day: Extra hours * 1.25
    Public Holiday: Hours * 1.5
    """
    mandatory_hours_per_day = 10
    
    # Calculate working days (26 or 27)
    if days_in_month == 31:
        expected_working_days = 27
    else:
        expected_working_days = 26
    
    mandatory_hours_per_month = mandatory_hours_per_day * expected_working_days
    
    # Separate public holiday and normal day hours
    public_holiday_hours = sum([flt(att.working_hours, 2) for att in attendance_list if att.is_public_holiday])
    normal_day_hours = total_hours - public_holiday_hours
    
    # Calculate extra hours on normal days
    extra_normal_hours = max(0, normal_day_hours - mandatory_hours_per_month)
    
    # Calculate OT
    normal_day_ot = extra_normal_hours * 1.25
    public_holiday_ot = public_holiday_hours * 1.5
    total_ot_amount = normal_day_ot + public_holiday_ot
    
    return {
        "category": "Category 3 - Admins (Branch Office)",
        "base_salary": base_salary,
        "total_working_hours": total_hours,
        "mandatory_hours": mandatory_hours_per_month,
        "normal_day_hours": normal_day_hours,
        "extra_normal_hours": extra_normal_hours,
        "public_holiday_hours": public_holiday_hours,
        "normal_day_ot": normal_day_ot,
        "public_holiday_ot": public_holiday_ot,
        "overtime_amount": total_ot_amount,
        "calculation_breakdown": {
            "normal_formula": f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
            "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
            "total": f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
        }
    }


def calculate_category_4(employee, base_salary, total_hours, attendance_list, days_in_month, start_date, end_date):
    """
    Category 4: Head Office
    Mandatory: 8 hours/day
    Weekend: Friday & Saturday
    Normal Day: Extra hours * 1.25
    Public Holiday: Hours * 1.5
    """
    mandatory_hours_per_day = 8
    
    # Calculate working days (excluding Friday and Saturday)
    working_days = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() not in [4, 5]:  # Not Friday(4) or Saturday(5)
            working_days += 1
        current_date += timedelta(days=1)
    
    mandatory_hours_per_month = mandatory_hours_per_day * working_days
    
    # Separate public holiday and normal day hours
    public_holiday_hours = sum([flt(att.working_hours, 2) for att in attendance_list if att.is_public_holiday])
    normal_day_hours = total_hours - public_holiday_hours
    
    # Calculate extra hours on normal days
    extra_normal_hours = max(0, normal_day_hours - mandatory_hours_per_month)
    
    # Calculate OT
    normal_day_ot = extra_normal_hours * 1.25
    public_holiday_ot = public_holiday_hours * 1.5
    total_ot_amount = normal_day_ot + public_holiday_ot
    
    return {
        "category": "Category 4 - Head Office",
        "base_salary": base_salary,
        "total_working_hours": total_hours,
        "mandatory_hours": mandatory_hours_per_month,
        "working_days": working_days,
        "normal_day_hours": normal_day_hours,
        "extra_normal_hours": extra_normal_hours,
        "public_holiday_hours": public_holiday_hours,
        "normal_day_ot": normal_day_ot,
        "public_holiday_ot": public_holiday_ot,
        "overtime_amount": total_ot_amount,
        "calculation_breakdown": {
            "normal_formula": f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
            "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
            "total": f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
        }
    }


def update_attendance_records(attendance_list, result):
    """
    Update individual attendance records with OT info
    """
    if not attendance_list:
        return
    
    extra_hours = result.get('extra_hours') or result.get('extra_normal_hours', 0)
    per_day_ot = 0
    
    if extra_hours > 0 and len(attendance_list) > 0:
        per_day_ot = result['overtime_amount'] / len(attendance_list)
    
    for att in attendance_list:
        frappe.db.set_value('Attendance', att.name, {
            'overtime_amount': per_day_ot
        }, update_modified=False)


@frappe.whitelist()
def create_additional_salary_for_overtime(employee, month, year):
    """
    Create Additional Salary entry for calculated overtime
    """
    month = int(month)
    year = int(year)
    # Calculate overtime
    ot_data = calculate_monthly_overtime(employee, month, year)
    
    if not ot_data or ot_data['overtime_amount'] <= 0:
        frappe.msgprint(_("No overtime amount to process"))
        return
    
    # Get or create Overtime Pay salary component
    if not frappe.db.exists("Salary Component", "Overtime Pay"):
        create_overtime_salary_component()
    
    # Get payroll date (last day of month)
    start_date = getdate(f"{year}-{month:02d}-01")
    payroll_date = get_last_day(start_date)
    
    # Check if Additional Salary already exists
    existing = frappe.db.exists("Additional Salary", {
        "employee": employee,
        "payroll_date": payroll_date,
        "salary_component": "Overtime Pay",
        "docstatus": ["<", 2]
    })
    
    if existing:
        doc = frappe.get_doc("Additional Salary", existing)
        doc.amount = ot_data['overtime_amount']
        doc.save()
        frappe.msgprint(_("Additional Salary updated: {0}").format(doc.name))
        return doc.name
    
    # Create new Additional Salary
    additional_salary = frappe.get_doc({
        "doctype": "Additional Salary",
        "employee": employee,
        "salary_component": "Overtime Pay",
        "amount": ot_data['overtime_amount'],
        "payroll_date": payroll_date,
        "company": frappe.defaults.get_user_default("Company"),
        "overwrite_salary_structure_amount": 0,
        "ref_doctype": "Attendance",
        "type": "Earning"
    })
    
    additional_salary.insert()
    
    frappe.msgprint(_("Additional Salary created: {0} - Amount: {1} BHD").format(
        additional_salary.name, 
        ot_data['overtime_amount']
    ))
    
    return additional_salary.name


def create_overtime_salary_component():
    """
    Create Overtime Pay salary component if it doesn't exist
    """
    salary_component = frappe.get_doc({
        "doctype": "Salary Component",
        "salary_component": "Overtime Pay",
        "salary_component_abbr": "OT",
        "type": "Earning",
        "is_flexible_benefit": 0,
        "is_tax_applicable": 1,
        "variable_based_on_taxable_salary": 0
    })
    salary_component.insert(ignore_if_duplicate=True)
    frappe.db.commit()


@frappe.whitelist()
def bulk_calculate_overtime(month, year, department=None):
    """
    Calculate overtime for all employees in a department/company
    """
    month = int(month)
    year = int(year)

    filters = {"status": "Active"}
    
    if department:
        filters["department"] = department
    
    employees = frappe.get_all("Employee", 
        filters=filters,
        fields=["name", "employee_name", "ot_category"]
    )
    
    results = []
    
    for emp in employees:
        if not emp.ot_category:
            continue
        
        try:
            ot_data = calculate_monthly_overtime(emp.name, int(month), int(year))
            results.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "category": emp.ot_category,
                "overtime_amount": ot_data['overtime_amount'],
                "total_hours": ot_data['total_working_hours'],
                "extra_hours": ot_data.get('extra_hours') or ot_data.get('extra_normal_hours', 0)
            })
        except Exception as e:
            frappe.log_error(f"Error calculating OT for {emp.name}: {str(e)}")
            continue
    
    return results


@frappe.whitelist()
def mark_public_holidays(from_date, to_date, holiday_list=None):
    """
    Mark attendance records as public holidays based on holiday list
    """
    if not holiday_list:
        holiday_list = frappe.get_value("Company", 
            frappe.defaults.get_user_default("Company"), 
            "default_holiday_list")
    
    if not holiday_list:
        frappe.throw(_("Please specify a holiday list"))
    
    # Get holidays from holiday list
    holidays = frappe.get_all("Holiday",
        filters={
            "parent": holiday_list,
            "holiday_date": ["between", [from_date, to_date]]
        },
        fields=["holiday_date"]
    )
    
    holiday_dates = [h.holiday_date for h in holidays]
    
    if not holiday_dates:
        frappe.msgprint(_("No holidays found in the specified period"))
        return
    
    # Update attendance records
    attendance_records = frappe.get_all("Attendance",
        filters={
            "attendance_date": ["in", holiday_dates],
            "status": "Present",
            "docstatus": 1
        },
        fields=["name"]
    )
    
    count = 0
    for att in attendance_records:
        frappe.db.set_value('Attendance', att.name, 'is_public_holiday', 1, update_modified=False)
        count += 1
    
    frappe.db.commit()
    frappe.msgprint(_("Marked {0} attendance records as public holidays").format(count))
    
    return count

import frappe
from frappe import _
from frappe.utils import flt, getdate, get_last_day
from datetime import datetime, timedelta
import calendar


@frappe.whitelist()
def calculate_monthly_overtime(employee, month, year):
    month = int(month)
    year = int(year)

    start_date = getdate(f"{year}-{month:02d}-01")
    end_date = get_last_day(start_date)
    days_in_month = calendar.monthrange(year, month)[1]

    employee_doc = frappe.get_doc("Employee", employee)
    ot_category = employee_doc.get('ot_category')

    if not ot_category:
        frappe.throw(_("Please set OT Category for employee {0}").format(employee_doc.employee_name))

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

    # Get attendance with shift info
    attendance_list = frappe.get_all("Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [start_date, end_date]],
            "status": "Present",
            "docstatus": 1
        },
        fields=["name", "attendance_date", "working_hours", "is_public_holiday", "shift"]
    )

    # Enrich each attendance with actual OT hours
    attendance_list = enrich_with_actual_ot_hours(attendance_list, employee)

    total_working_hours = sum([flt(att.working_hours, 2) for att in attendance_list])

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

    update_attendance_records(attendance_list, result)
    return result


# ============================================================
#  CORE — Get all checkin pairs and calculate OT from shift end
# ============================================================
def get_checkin_pairs(employee, date, shift_start_dt, shift_end_dt):
    """
    Fetch all Employee Checkin records for the day and pair IN/OUT.
    Returns:
        pairs          — list of (in_time, out_time) tuples
        total_worked   — total hours worked (sum of all valid pairs)
        total_break    — total break time between pairs in hours
        allowed_break  — standard allowed break (2 hours)
        excess_break   — break beyond allowed (reduces OT eligibility)
        after_shift_hours — hours worked strictly after shift end time
    """
    # Fetch all checkins for this day — extend window for overnight shifts
    day_start = shift_start_dt - timedelta(hours=2)
    day_end   = shift_end_dt + timedelta(hours=12)

    checkins = frappe.get_all("Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", [
                day_start.strftime("%Y-%m-%d %H:%M:%S"),
                day_end.strftime("%Y-%m-%d %H:%M:%S")
            ]]
        },
        fields=["name", "log_type", "time"],
        order_by="time asc"
    )

    if not checkins:
        return [], 0.0, 0.0, 2.0, 0.0, 0.0

    # Convert time strings to datetime
    for c in checkins:
        if isinstance(c.time, str):
            c.time = datetime.strptime(c.time, "%Y-%m-%d %H:%M:%S")

    # Build IN/OUT pairs
    pairs = []
    i = 0
    while i < len(checkins):
        if checkins[i].log_type == "IN":
            in_time = checkins[i].time
            # Find matching OUT
            j = i + 1
            while j < len(checkins):
                if checkins[j].log_type == "OUT":
                    out_time = checkins[j].time
                    pairs.append((in_time, out_time))
                    i = j + 1
                    break
                j += 1
            else:
                i += 1
        else:
            i += 1

    if not pairs:
        return [], 0.0, 0.0, 2.0, 0.0, 0.0

    # Total worked hours = sum of all IN-OUT durations
    total_worked = sum(
        (out - inn).total_seconds() / 3600
        for inn, out in pairs
    )

    # Total break = gaps between consecutive pairs
    total_break = 0.0
    for idx in range(1, len(pairs)):
        prev_out = pairs[idx - 1][1]
        curr_in  = pairs[idx][0]
        gap = (curr_in - prev_out).total_seconds() / 3600
        if gap > 0:
            total_break += gap

    allowed_break = 2.0  # Standard 2-hour break allowed
    excess_break  = max(0.0, total_break - allowed_break)

    # Hours worked AFTER shift end time
    # Only count segments or portions of segments that fall after shift_end_dt
    after_shift_seconds = 0.0
    for inn, out in pairs:
        if out <= shift_end_dt:
            # Entire segment is within shift — no OT
            continue
        elif inn >= shift_end_dt:
            # Entire segment is after shift end
            after_shift_seconds += (out - inn).total_seconds()
        else:
            # Segment straddles shift end — only count portion after shift end
            after_shift_seconds += (out - shift_end_dt).total_seconds()

    after_shift_hours = after_shift_seconds / 3600

    # Reduce after-shift hours by excess break time
    # If employee took 3h break and standard is 2h,
    # that 1h excess break reduces their OT eligibility
    after_shift_hours = max(0.0, after_shift_hours - excess_break)

    return pairs, total_worked, total_break, allowed_break, excess_break, after_shift_hours


def enrich_with_actual_ot_hours(attendance_list, employee):
    """
    For each attendance record:
    1. Get shift and its start/end times
    2. Get all check-in/out pairs for the day
    3. Calculate hours worked after shift end
    4. Subtract excess break (break > 2 hours)
    5. Apply 1-hour minimum — floor to whole hours
    """
    for att in attendance_list:
        att.ot_hours        = 0.0
        att.shift_end_time  = None
        att.last_checkout   = None
        att.total_break     = 0.0
        att.excess_break    = 0.0
        att.after_shift_raw = 0.0

        try:
            shift_name = att.get('shift')

            # Fallback to Shift Assignment if not on attendance
            if not shift_name:
                shift_name = frappe.db.get_value(
                    "Shift Assignment",
                    {
                        "employee": employee,
                        "start_date": ["<=", att.attendance_date],
                        "docstatus": 1,
                        "status": "Active"
                    },
                    "shift_type",
                    order_by="start_date desc"
                )

            if not shift_name:
                # No shift — fallback to working_hours field
                att.ot_hours = 0.0
                continue

            shift = frappe.get_doc("Shift Type", shift_name)
            attendance_date = getdate(att.attendance_date)

            # Build shift start and end datetimes
            shift_start_dt = datetime.combine(attendance_date, datetime.min.time()) + shift.start_time
            shift_end_dt   = datetime.combine(attendance_date, datetime.min.time()) + shift.end_time

            # Handle overnight shifts
            if shift.end_time < shift.start_time:
                shift_end_dt += timedelta(days=1)

            att.shift_end_time  = shift_end_dt
            att.shift_start_time = shift_start_dt

            # Get all checkin pairs and calculate OT
            pairs, total_worked, total_break, allowed_break, excess_break, after_shift_hours = \
                get_checkin_pairs(employee, attendance_date, shift_start_dt, shift_end_dt)

            att.checkin_pairs   = len(pairs)
            att.total_worked    = round(total_worked, 2)
            att.total_break     = round(total_break, 2)
            att.allowed_break   = allowed_break
            att.excess_break    = round(excess_break, 2)
            att.after_shift_raw = round(after_shift_hours, 2)

            # Apply 1-hour minimum and floor to whole hours
            if after_shift_hours >= 1.0:
                att.ot_hours = float(int(after_shift_hours))
            else:
                att.ot_hours = 0.0

        except Exception as e:
            frappe.log_error(
                f"OT enrichment error for attendance {att.name} "
                f"employee {employee}: {str(e)}"
            )
            att.ot_hours = 0.0

    return attendance_list


# ============================================================
#  DAILY EXTRA HOURS — uses shift-based ot_hours
# ============================================================
def get_daily_extra_hours(attendance_list, mandatory_hours_per_day):
    normal_extra  = 0.0
    holiday_extra = 0.0
    per_day_detail = []

    for att in attendance_list:
        hours    = flt(att.working_hours, 2)
        ot_hours = flt(att.get('ot_hours', 0), 2)

        if att.is_public_holiday:
            # Public holiday: all working hours count, no minimum
            holiday_extra += hours
            per_day_detail.append({
                "date":            str(att.attendance_date),
                "hours":           hours,
                "type":            "public_holiday",
                "eligible_extra":  hours,
                "note":            "Public holiday — all hours eligible"
            })
        else:
            normal_extra += ot_hours
            per_day_detail.append({
                "date":              str(att.attendance_date),
                "hours":             hours,
                "type":              "normal",
                "shift_end":         str(att.get('shift_end_time', 'N/A')),
                "total_break":       att.get('total_break', 0),
                "allowed_break":     att.get('allowed_break', 2),
                "excess_break":      att.get('excess_break', 0),
                "after_shift_raw":   att.get('after_shift_raw', 0),
                "eligible_extra":    ot_hours,
                "note": (
                    "Eligible for OT" if ot_hours > 0
                    else "Not eligible — less than 1hr after shift end or excess break"
                )
            })

    return normal_extra, holiday_extra, per_day_detail


# ============================================================
#  CATEGORY CALCULATIONS
# ============================================================
def calculate_category_1(employee, gross_salary, total_hours, attendance_list, days_in_month):
    mandatory_hours_per_day = 10
    extra_hours, holiday_hours, per_day_detail = get_daily_extra_hours(
        attendance_list, mandatory_hours_per_day
    )
    total_extra     = extra_hours + holiday_hours
    daily_rate      = gross_salary / 30
    hourly_rate     = daily_rate / mandatory_hours_per_day
    overtime_amount = hourly_rate * total_extra

    return {
        "category":               "Category 1 - Cleaners & Serviceman",
        "gross_salary":           gross_salary,
        "total_working_hours":    total_hours,
        "mandatory_hours_per_day": mandatory_hours_per_day,
        "extra_hours":            total_extra,
        "hourly_rate":            hourly_rate,
        "overtime_amount":        overtime_amount,
        "per_day_detail":         per_day_detail,
        "calculation_breakdown": {
            "daily_rate":  daily_rate,
            "hourly_rate": hourly_rate,
            "formula": (
                f"{gross_salary}/30 = {daily_rate:.3f}, "
                f"{daily_rate:.3f}/10 = {hourly_rate:.3f}, "
                f"{hourly_rate:.3f} * {total_extra} = {overtime_amount:.3f}"
            )
        }
    }


def calculate_category_2(employee, base_salary, total_hours, attendance_list, days_in_month):
    mandatory_hours_per_day = 8
    extra_normal_hours, public_holiday_hours, per_day_detail = get_daily_extra_hours(
        attendance_list, mandatory_hours_per_day
    )
    normal_day_ot     = extra_normal_hours * 1.25
    public_holiday_ot = public_holiday_hours * 1.5
    total_ot_amount   = normal_day_ot + public_holiday_ot

    return {
        "category":               "Category 2 - Lazer VTC",
        "base_salary":            base_salary,
        "total_working_hours":    total_hours,
        "mandatory_hours_per_day": mandatory_hours_per_day,
        "extra_normal_hours":     extra_normal_hours,
        "public_holiday_hours":   public_holiday_hours,
        "normal_day_ot":          normal_day_ot,
        "public_holiday_ot":      public_holiday_ot,
        "overtime_amount":        total_ot_amount,
        "per_day_detail":         per_day_detail,
        "calculation_breakdown": {
            "normal_formula":  f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
            "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
            "total":           f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
        }
    }


def calculate_category_3(employee, base_salary, total_hours, attendance_list, days_in_month):
    mandatory_hours_per_day = 10
    extra_normal_hours, public_holiday_hours, per_day_detail = get_daily_extra_hours(
        attendance_list, mandatory_hours_per_day
    )
    normal_day_ot     = extra_normal_hours * 1.25
    public_holiday_ot = public_holiday_hours * 1.5
    total_ot_amount   = normal_day_ot + public_holiday_ot

    return {
        "category":               "Category 3 - Admins (Branch Office)",
        "base_salary":            base_salary,
        "total_working_hours":    total_hours,
        "mandatory_hours_per_day": mandatory_hours_per_day,
        "extra_normal_hours":     extra_normal_hours,
        "public_holiday_hours":   public_holiday_hours,
        "normal_day_ot":          normal_day_ot,
        "public_holiday_ot":      public_holiday_ot,
        "overtime_amount":        total_ot_amount,
        "per_day_detail":         per_day_detail,
        "calculation_breakdown": {
            "normal_formula":  f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
            "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
            "total":           f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
        }
    }


def calculate_category_4(employee, base_salary, total_hours, attendance_list,
                          days_in_month, start_date, end_date):
    mandatory_hours_per_day = 8

    working_days = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() not in [4, 5]:
            working_days += 1
        current_date += timedelta(days=1)

    extra_normal_hours, public_holiday_hours, per_day_detail = get_daily_extra_hours(
        attendance_list, mandatory_hours_per_day
    )
    normal_day_ot     = extra_normal_hours * 1.25
    public_holiday_ot = public_holiday_hours * 1.5
    total_ot_amount   = normal_day_ot + public_holiday_ot

    return {
        "category":               "Category 4 - Head Office",
        "base_salary":            base_salary,
        "total_working_hours":    total_hours,
        "mandatory_hours_per_day": mandatory_hours_per_day,
        "working_days":           working_days,
        "extra_normal_hours":     extra_normal_hours,
        "public_holiday_hours":   public_holiday_hours,
        "normal_day_ot":          normal_day_ot,
        "public_holiday_ot":      public_holiday_ot,
        "overtime_amount":        total_ot_amount,
        "per_day_detail":         per_day_detail,
        "calculation_breakdown": {
            "normal_formula":  f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
            "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
            "total":           f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
        }
    }


# ============================================================
#  UPDATE ATTENDANCE RECORDS
# ============================================================
def update_attendance_records(attendance_list, result):
    if not attendance_list:
        return

    extra_hours = result.get('extra_hours') or result.get('extra_normal_hours', 0)
    per_day_ot  = 0

    if extra_hours > 0 and len(attendance_list) > 0:
        per_day_ot = result['overtime_amount'] / len(attendance_list)

    for att in attendance_list:
        frappe.db.set_value('Attendance', att.name, {
            'overtime_amount': per_day_ot
        }, update_modified=False)


# ============================================================
#  REMAINING ENDPOINTS
# ============================================================
@frappe.whitelist()
def create_additional_salary_for_overtime(employee, month, year):
    month = int(month)
    year  = int(year)

    ot_data = calculate_monthly_overtime(employee, month, year)

    if not ot_data or ot_data['overtime_amount'] <= 0:
        frappe.msgprint(_("No overtime amount to process"))
        return

    if not frappe.db.exists("Salary Component", "Overtime Pay"):
        create_overtime_salary_component()

    start_date   = getdate(f"{year}-{month:02d}-01")
    payroll_date = get_last_day(start_date)

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
    month = int(month)
    year  = int(year)

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
                "employee":       emp.name,
                "employee_name":  emp.employee_name,
                "category":       emp.ot_category,
                "overtime_amount": ot_data['overtime_amount'],
                "total_hours":    ot_data['total_working_hours'],
                "extra_hours":    ot_data.get('extra_hours') or ot_data.get('extra_normal_hours', 0)
            })
        except Exception as e:
            frappe.log_error(f"Error calculating OT for {emp.name}: {str(e)}")
            continue

    return results


@frappe.whitelist()
def mark_public_holidays(from_date, to_date, holiday_list=None):
    if not holiday_list:
        holiday_list = frappe.get_value("Company",
            frappe.defaults.get_user_default("Company"),
            "default_holiday_list")

    if not holiday_list:
        frappe.throw(_("Please specify a holiday list"))

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
        frappe.db.set_value('Attendance', att.name, 'is_public_holiday', 1,
                            update_modified=False)
        count += 1

    frappe.db.commit()
    frappe.msgprint(_("Marked {0} attendance records as public holidays").format(count))
    return count

# import frappe
# from frappe import _
# from frappe.utils import flt, getdate, get_last_day, date_diff
# from datetime import datetime, timedelta
# import calendar

# @frappe.whitelist()
# def calculate_monthly_overtime(employee, month, year):
#     """
#     Calculate overtime for an employee for entire month based on their category
#     """
#     month = int(month)
#     year = int(year)

#     # Get month start and end dates
#     start_date = getdate(f"{year}-{month:02d}-01")
#     end_date = get_last_day(start_date)
#     days_in_month = calendar.monthrange(year, month)[1]

#     # Get employee details
#     employee_doc = frappe.get_doc("Employee", employee)
#     ot_category = employee_doc.get('ot_category')

#     if not ot_category:
#         frappe.throw(_("Please set OT Category for employee {0}").format(employee_doc.employee_name))

#     # Get salary details
#     salary_assignment = frappe.get_value(
#         "Salary Structure Assignment",
#         {
#             "employee": employee,
#             "docstatus": 1,
#             "from_date": ["<=", end_date]
#         },
#         ["base", "gross_salary"],
#         as_dict=1,
#         order_by="from_date desc"
#     )

#     if not salary_assignment:
#         frappe.throw(_("No active salary structure found for employee {0}").format(employee_doc.employee_name))

#     base_salary = flt(salary_assignment.base)
#     gross_salary = flt(salary_assignment.gross_salary) or base_salary

#     # Get all attendance for the month
#     attendance_list = frappe.get_all("Attendance",
#         filters={
#             "employee": employee,
#             "attendance_date": ["between", [start_date, end_date]],
#             "status": "Present",
#             "docstatus": 1
#         },
#         fields=["name", "attendance_date", "working_hours", "is_public_holiday"]
#     )

#     # Calculate total working hours
#     total_working_hours = sum([flt(att.working_hours, 2) for att in attendance_list])

#     # Calculate based on category
#     if ot_category == "Category 1 - Cleaners & Serviceman":
#         result = calculate_category_1(employee_doc, gross_salary, total_working_hours,
#                                        attendance_list, days_in_month)

#     elif ot_category == "Category 2 - Lazer VTC":
#         result = calculate_category_2(employee_doc, base_salary, total_working_hours,
#                                        attendance_list, days_in_month)

#     elif ot_category == "Category 3 - Admins (Branch Office)":
#         result = calculate_category_3(employee_doc, base_salary, total_working_hours,
#                                        attendance_list, days_in_month)

#     elif ot_category == "Category 4 - Head Office":
#         result = calculate_category_4(employee_doc, base_salary, total_working_hours,
#                                        attendance_list, days_in_month, start_date, end_date)
#     else:
#         frappe.throw(_("Invalid OT Category"))

#     # Update attendance records with OT details
#     update_attendance_records(attendance_list, result)

#     return result


# # ============================================================
# #  CORE HELPER — per-day extra hours with 1-hour minimum
# # ============================================================
# def get_daily_extra_hours(attendance_list, mandatory_hours_per_day):
#     """
#     For each attendance record, calculate extra hours worked beyond
#     mandatory_hours_per_day. An employee must work at least
#     (mandatory_hours_per_day + 1) full hour beyond shift to earn ANY
#     OT for that day — partial hours under 1 are discarded per day.

#     Returns:
#         normal_extra  — eligible extra hours on normal days (floored per day)
#         holiday_extra — ALL hours on public holiday days (no floor applied,
#                         public holidays are fully paid regardless)
#         per_day_detail — list of dicts for debugging
#     """
#     normal_extra  = 0.0
#     holiday_extra = 0.0
#     per_day_detail = []

#     for att in attendance_list:
#         hours = flt(att.working_hours, 2)

#         if att.is_public_holiday:
#             # Public holiday: all hours count, no minimum threshold
#             holiday_extra += hours
#             per_day_detail.append({
#                 "date": str(att.attendance_date),
#                 "hours": hours,
#                 "type": "public_holiday",
#                 "eligible_extra": hours
#             })
#         else:
#             # Normal day: must exceed mandatory + 1 full hour
#             raw_extra = hours - mandatory_hours_per_day
#             if raw_extra >= 1.0:
#                 # Floor to whole hours — ignore sub-hour remainder
#                 eligible = int(raw_extra)
#                 normal_extra += eligible
#                 per_day_detail.append({
#                     "date": str(att.attendance_date),
#                     "hours": hours,
#                     "type": "normal",
#                     "raw_extra": raw_extra,
#                     "eligible_extra": eligible
#                 })
#             else:
#                 per_day_detail.append({
#                     "date": str(att.attendance_date),
#                     "hours": hours,
#                     "type": "normal",
#                     "raw_extra": max(0, raw_extra),
#                     "eligible_extra": 0,
#                     "note": "Below 1-hour minimum — not eligible"
#                 })

#     return normal_extra, holiday_extra, per_day_detail


# def calculate_category_1(employee, gross_salary, total_hours, attendance_list, days_in_month):
#     """
#     Category 1: Cleaners & Serviceman
#     Mandatory: 10 hours/day
#     Formula: (Gross Salary / 30) / 10 * Extra Hours
#     Per-day minimum: must work > 10h + 1h to get OT that day.
#     """
#     mandatory_hours_per_day = 10

#     extra_hours, holiday_hours, per_day_detail = get_daily_extra_hours(
#         attendance_list, mandatory_hours_per_day
#     )
#     # Category 1 does not differentiate public holidays — add them in
#     total_extra = extra_hours + holiday_hours

#     daily_rate   = gross_salary / 30
#     hourly_rate  = daily_rate / mandatory_hours_per_day
#     overtime_amount = hourly_rate * total_extra

#     return {
#         "category": "Category 1 - Cleaners & Serviceman",
#         "gross_salary": gross_salary,
#         "total_working_hours": total_hours,
#         "mandatory_hours_per_day": mandatory_hours_per_day,
#         "extra_hours": total_extra,
#         "hourly_rate": hourly_rate,
#         "overtime_amount": overtime_amount,
#         "per_day_detail": per_day_detail,
#         "calculation_breakdown": {
#             "daily_rate": daily_rate,
#             "hourly_rate": hourly_rate,
#             "formula": (
#                 f"{gross_salary}/30 = {daily_rate:.3f}, "
#                 f"{daily_rate:.3f}/10 = {hourly_rate:.3f}, "
#                 f"{hourly_rate:.3f} * {total_extra} = {overtime_amount:.3f}"
#             )
#         }
#     }


# def calculate_category_2(employee, base_salary, total_hours, attendance_list, days_in_month):
#     """
#     Category 2: Lazer VTC
#     Mandatory: 8 hours/day
#     Normal Day extra: floor to whole hours, minimum 1h per day
#     Public Holiday: all hours * 1.5 (no minimum threshold)
#     """
#     mandatory_hours_per_day = 8

#     extra_normal_hours, public_holiday_hours, per_day_detail = get_daily_extra_hours(
#         attendance_list, mandatory_hours_per_day
#     )

#     normal_day_ot    = extra_normal_hours * 1.25
#     public_holiday_ot = public_holiday_hours * 1.5
#     total_ot_amount  = normal_day_ot + public_holiday_ot

#     return {
#         "category": "Category 2 - Lazer VTC",
#         "base_salary": base_salary,
#         "total_working_hours": total_hours,
#         "mandatory_hours_per_day": mandatory_hours_per_day,
#         "extra_normal_hours": extra_normal_hours,
#         "public_holiday_hours": public_holiday_hours,
#         "normal_day_ot": normal_day_ot,
#         "public_holiday_ot": public_holiday_ot,
#         "overtime_amount": total_ot_amount,
#         "per_day_detail": per_day_detail,
#         "calculation_breakdown": {
#             "normal_formula": f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
#             "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
#             "total": f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
#         }
#     }


# def calculate_category_3(employee, base_salary, total_hours, attendance_list, days_in_month):
#     """
#     Category 3: Admins (Branch Office)
#     Mandatory: 10 hours/day
#     Normal Day extra: floor to whole hours, minimum 1h per day
#     Public Holiday: all hours * 1.5 (no minimum threshold)
#     """
#     mandatory_hours_per_day = 10

#     extra_normal_hours, public_holiday_hours, per_day_detail = get_daily_extra_hours(
#         attendance_list, mandatory_hours_per_day
#     )

#     normal_day_ot     = extra_normal_hours * 1.25
#     public_holiday_ot = public_holiday_hours * 1.5
#     total_ot_amount   = normal_day_ot + public_holiday_ot

#     return {
#         "category": "Category 3 - Admins (Branch Office)",
#         "base_salary": base_salary,
#         "total_working_hours": total_hours,
#         "mandatory_hours_per_day": mandatory_hours_per_day,
#         "extra_normal_hours": extra_normal_hours,
#         "public_holiday_hours": public_holiday_hours,
#         "normal_day_ot": normal_day_ot,
#         "public_holiday_ot": public_holiday_ot,
#         "overtime_amount": total_ot_amount,
#         "per_day_detail": per_day_detail,
#         "calculation_breakdown": {
#             "normal_formula": f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
#             "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
#             "total": f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
#         }
#     }


# def calculate_category_4(employee, base_salary, total_hours, attendance_list, days_in_month, start_date, end_date):
#     """
#     Category 4: Head Office
#     Mandatory: 8 hours/day (weekdays only, Fri & Sat are weekend)
#     Normal Day extra: floor to whole hours, minimum 1h per day
#     Public Holiday: all hours * 1.5 (no minimum threshold)
#     """
#     mandatory_hours_per_day = 8

#     # Count working days excluding Friday(4) and Saturday(5)
#     working_days = 0
#     current_date = start_date
#     while current_date <= end_date:
#         if current_date.weekday() not in [4, 5]:
#             working_days += 1
#         current_date += timedelta(days=1)

#     extra_normal_hours, public_holiday_hours, per_day_detail = get_daily_extra_hours(
#         attendance_list, mandatory_hours_per_day
#     )

#     normal_day_ot     = extra_normal_hours * 1.25
#     public_holiday_ot = public_holiday_hours * 1.5
#     total_ot_amount   = normal_day_ot + public_holiday_ot

#     return {
#         "category": "Category 4 - Head Office",
#         "base_salary": base_salary,
#         "total_working_hours": total_hours,
#         "mandatory_hours_per_day": mandatory_hours_per_day,
#         "working_days": working_days,
#         "extra_normal_hours": extra_normal_hours,
#         "public_holiday_hours": public_holiday_hours,
#         "normal_day_ot": normal_day_ot,
#         "public_holiday_ot": public_holiday_ot,
#         "overtime_amount": total_ot_amount,
#         "per_day_detail": per_day_detail,
#         "calculation_breakdown": {
#             "normal_formula": f"{extra_normal_hours} * 1.25 = {normal_day_ot:.3f}",
#             "holiday_formula": f"{public_holiday_hours} * 1.5 = {public_holiday_ot:.3f}",
#             "total": f"{normal_day_ot:.3f} + {public_holiday_ot:.3f} = {total_ot_amount:.3f}"
#         }
#     }


# def update_attendance_records(attendance_list, result):
#     """
#     Update individual attendance records with OT info
#     """
#     if not attendance_list:
#         return

#     extra_hours = result.get('extra_hours') or result.get('extra_normal_hours', 0)
#     per_day_ot  = 0

#     if extra_hours > 0 and len(attendance_list) > 0:
#         per_day_ot = result['overtime_amount'] / len(attendance_list)

#     for att in attendance_list:
#         frappe.db.set_value('Attendance', att.name, {
#             'overtime_amount': per_day_ot
#         }, update_modified=False)


# @frappe.whitelist()
# def create_additional_salary_for_overtime(employee, month, year):
#     """
#     Create Additional Salary entry for calculated overtime
#     """
#     month = int(month)
#     year  = int(year)

#     ot_data = calculate_monthly_overtime(employee, month, year)

#     if not ot_data or ot_data['overtime_amount'] <= 0:
#         frappe.msgprint(_("No overtime amount to process"))
#         return

#     if not frappe.db.exists("Salary Component", "Overtime Pay"):
#         create_overtime_salary_component()

#     start_date   = getdate(f"{year}-{month:02d}-01")
#     payroll_date = get_last_day(start_date)

#     existing = frappe.db.exists("Additional Salary", {
#         "employee": employee,
#         "payroll_date": payroll_date,
#         "salary_component": "Overtime Pay",
#         "docstatus": ["<", 2]
#     })

#     if existing:
#         doc = frappe.get_doc("Additional Salary", existing)
#         doc.amount = ot_data['overtime_amount']
#         doc.save()
#         frappe.msgprint(_("Additional Salary updated: {0}").format(doc.name))
#         return doc.name

#     additional_salary = frappe.get_doc({
#         "doctype": "Additional Salary",
#         "employee": employee,
#         "salary_component": "Overtime Pay",
#         "amount": ot_data['overtime_amount'],
#         "payroll_date": payroll_date,
#         "company": frappe.defaults.get_user_default("Company"),
#         "overwrite_salary_structure_amount": 0,
#         "ref_doctype": "Attendance",
#         "type": "Earning"
#     })

#     additional_salary.insert()

#     frappe.msgprint(_("Additional Salary created: {0} - Amount: {1} BHD").format(
#         additional_salary.name,
#         ot_data['overtime_amount']
#     ))

#     return additional_salary.name


# def create_overtime_salary_component():
#     """
#     Create Overtime Pay salary component if it doesn't exist
#     """
#     salary_component = frappe.get_doc({
#         "doctype": "Salary Component",
#         "salary_component": "Overtime Pay",
#         "salary_component_abbr": "OT",
#         "type": "Earning",
#         "is_flexible_benefit": 0,
#         "is_tax_applicable": 1,
#         "variable_based_on_taxable_salary": 0
#     })
#     salary_component.insert(ignore_if_duplicate=True)
#     frappe.db.commit()


# @frappe.whitelist()
# def bulk_calculate_overtime(month, year, department=None):
#     """
#     Calculate overtime for all employees in a department/company
#     """
#     month = int(month)
#     year  = int(year)

#     filters = {"status": "Active"}
#     if department:
#         filters["department"] = department

#     employees = frappe.get_all("Employee",
#         filters=filters,
#         fields=["name", "employee_name", "ot_category"]
#     )

#     results = []

#     for emp in employees:
#         if not emp.ot_category:
#             continue
#         try:
#             ot_data = calculate_monthly_overtime(emp.name, int(month), int(year))
#             results.append({
#                 "employee": emp.name,
#                 "employee_name": emp.employee_name,
#                 "category": emp.ot_category,
#                 "overtime_amount": ot_data['overtime_amount'],
#                 "total_hours": ot_data['total_working_hours'],
#                 "extra_hours": ot_data.get('extra_hours') or ot_data.get('extra_normal_hours', 0)
#             })
#         except Exception as e:
#             frappe.log_error(f"Error calculating OT for {emp.name}: {str(e)}")
#             continue

#     return results


# @frappe.whitelist()
# def mark_public_holidays(from_date, to_date, holiday_list=None):
#     """
#     Mark attendance records as public holidays based on holiday list
#     """
#     if not holiday_list:
#         holiday_list = frappe.get_value("Company",
#             frappe.defaults.get_user_default("Company"),
#             "default_holiday_list")

#     if not holiday_list:
#         frappe.throw(_("Please specify a holiday list"))

#     holidays = frappe.get_all("Holiday",
#         filters={
#             "parent": holiday_list,
#             "holiday_date": ["between", [from_date, to_date]]
#         },
#         fields=["holiday_date"]
#     )

#     holiday_dates = [h.holiday_date for h in holidays]

#     if not holiday_dates:
#         frappe.msgprint(_("No holidays found in the specified period"))
#         return

#     attendance_records = frappe.get_all("Attendance",
#         filters={
#             "attendance_date": ["in", holiday_dates],
#             "status": "Present",
#             "docstatus": 1
#         },
#         fields=["name"]
#     )

#     count = 0
#     for att in attendance_records:
#         frappe.db.set_value('Attendance', att.name, 'is_public_holiday', 1, update_modified=False)
#         count += 1

#     frappe.db.commit()
#     frappe.msgprint(_("Marked {0} attendance records as public holidays").format(count))

#     return count
# Copyright (c) 2025, eldho.mathew@webtreeonline.com and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import getdate, flt
import frappe


class EmployeeIndemnitySettlement(Document):

    def before_save(self):
        self.calculate_indemnity()

    def calculate_indemnity(self):
        """
        Bahrain Indemnity Calculation
        -----------------------------
        Year 1–3 : 15 days salary per year (0.5 month)
        Year 4+  : 1 full month salary per year
        """

        # -----------------------------
        # Basic validations
        # -----------------------------
        if not self.employee:
            self.total_indemnity = 0
            return

        if not self.date_of_joining or not self.relieving_date:
            self.total_indemnity = 0
            return

        # ✅ convert salary safely (string → float)
        salary = flt(self.indemnity_salary)

        if salary <= 0:
            self.total_indemnity = 0
            return

        # -----------------------------
        # Convert date strings → date objects
        # -----------------------------
        try:
            join_date = getdate(self.date_of_joining)
            relieving_date = getdate(self.relieving_date)
        except Exception:
            frappe.throw("Invalid Date of Joining or Relieving Date")

        if relieving_date <= join_date:
            frappe.throw("Relieving Date must be after Date of Joining")

        # -----------------------------
        # Calculate service duration
        # -----------------------------
        total_days = (relieving_date - join_date).days
        full_years = total_days // 365
        remaining_days = total_days % 365

        total = 0.0

        # -----------------------------
        # Years 1–3 → 15 days (0.5 month)
        # -----------------------------
        first_years = min(full_years, 3)
        total += first_years * (salary * 0.5)

        # -----------------------------
        # From 4th year → 1 month
        # -----------------------------
        if full_years > 3:
            total += (full_years - 3) * salary

        # -----------------------------
        # Partial year calculation
        # -----------------------------
        if remaining_days > 0:
            if full_years < 3:
                total += (salary * 0.5) * (remaining_days / 365)
            else:
                total += salary * (remaining_days / 365)

        # -----------------------------
        # Final result
        # -----------------------------
        self.total_indemnity = round(total, 3)

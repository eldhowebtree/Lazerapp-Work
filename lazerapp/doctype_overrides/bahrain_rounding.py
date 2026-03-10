import frappe
from decimal import Decimal, ROUND_HALF_UP

def apply_bahrain_rounding(doc, method=None):
    """Apply Bahrain rounding (3 decimal precision) for BHD currency."""
    if not doc.currency or doc.currency != "BHD":
        return  # Only apply for Bahrain Dinar (BHD)

    grand_total = float(doc.grand_total or 0)

    # ✅ Use financial rounding (half up)
    rounded_total = float(Decimal(str(grand_total)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))
    rounding_adjustment = rounded_total - grand_total

    # Update standard fields
    doc.rounded_total = rounded_total
    doc.rounding_adjustment = rounding_adjustment

    # Update base fields if available
    if hasattr(doc, "base_rounded_total"):
        doc.base_rounded_total = rounded_total
    if hasattr(doc, "base_rounding_adjustment"):
        doc.base_rounding_adjustment = rounding_adjustment

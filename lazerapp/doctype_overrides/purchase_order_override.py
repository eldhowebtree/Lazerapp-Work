import frappe
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder

class CustomPurchaseOrder(PurchaseOrder):
    def before_save(self):
        """Automatically calculate total amount including VAT before saving."""
        self.update_amount_with_vat()

    def update_amount_with_vat(self):
        """Add custom_vat_bd to each item's amount and update totals."""
        if not self.items:
            return

        total = 0.0

        for item in self.items:
            rate = float(item.rate or 0)
            qty = float(item.qty or 0)
            vat_bd = float(item.custom_vat_bd or 0)

            # ✅ Correct calculation
            amount = (rate * qty) + vat_bd
            item.amount = amount

            total += amount

        # ✅ Update total fields on parent Purchase Order
        self.total = total
        self.grand_total = total
        self.base_grand_total = total

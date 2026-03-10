import frappe
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt


class CustomPurchaseReceipt(PurchaseReceipt):

    def before_save(self):
        self.update_amount_with_vat()

    def before_submit(self):
        """
        FINAL sync before stock posting
        """
        self.sync_qty_with_custom_quantity()
        self.update_amount_with_vat()

    def sync_qty_with_custom_quantity(self):
        """
        Ensure ERPNext uses correct quantity on submit
        """
        for item in self.items:
            if item.custom_quantity:
                item.qty = item.custom_quantity

    def update_amount_with_vat(self):
        """
        amount = (rate * custom_quantity) + custom_vat_bd
        """
        total = 0.0

        for item in self.items:
            rate = float(item.rate or 0)
            qty = float(item.custom_quantity or 0)
            vat = float(item.custom_vat_bd or 0)

            item.amount = (rate * qty) + vat
            total += item.amount

        self.total = total
        self.grand_total = total
        self.base_grand_total = total

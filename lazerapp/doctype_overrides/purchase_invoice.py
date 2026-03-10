import frappe
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice


class CustomPurchaseInvoice(PurchaseInvoice):

    def before_insert(self):
        """
        Capture GRN numbers automatically when PI is created from GRN
        """
        self.set_grn_nos()

    def before_save(self):
        """
        Safety: ensure GRN numbers stay in sync
        """
        self.set_grn_nos()

    def set_grn_nos(self):
        """
        Collect unique Purchase Receipt numbers from items
        """
        grns = set()

        for item in self.items:
            if item.purchase_receipt:
                grns.add(item.purchase_receipt)

        if grns:
            # Store comma-separated GRNs for client visibility
            self.custom_grn_nos = ", ".join(sorted(grns))

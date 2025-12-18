# import frappe
# from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry as ERPNextPaymentEntry


# class PaymentEntry(ERPNextPaymentEntry):
#     pass


# @frappe.whitelist()
# def get_outstanding_grn(party, company, from_date=None, to_date=None, min_outstanding=0):
#     if not party or not company:
#         return []

#     conditions = """
#         pr.docstatus = 1
#         AND pr.supplier = %(party)s
#         AND pr.company = %(company)s
#         AND pr.per_billed < 100
#     """

#     if from_date:
#         conditions += " AND pr.posting_date >= %(from_date)s"
#     if to_date:
#         conditions += " AND pr.posting_date <= %(to_date)s"

#     return frappe.db.sql(
#         f"""
#         SELECT
#             pr.name,
#             pr.posting_date,
#             pr.grand_total,
#             ROUND(pr.grand_total * (100 - IFNULL(pr.per_billed, 0)) / 100, 2) AS outstanding_amount
#         FROM `tabPurchase Receipt` pr
#         WHERE {conditions}
#         HAVING outstanding_amount > %(min_outstanding)s
#         ORDER BY pr.posting_date ASC
#         """,
#         {
#             "party": party,
#             "company": company,
#             "from_date": from_date,
#             "to_date": to_date,
#             "min_outstanding": min_outstanding or 0,
#         },
#         as_dict=True,
#     )

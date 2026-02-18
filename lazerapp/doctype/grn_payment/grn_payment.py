# Copyright (c) 2025, eldho.mathew@webtreeonline.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GRNPayment(Document):
    pass


@frappe.whitelist()
def get_outstanding_grn_orders(
    supplier=None,
    company=None,
    from_date=None,
    to_date=None,
    min_outstanding=0
):
    if not supplier or not company:
        return []

    conditions = """
        pr.docstatus = 1
        AND pr.supplier = %(supplier)s
        AND pr.company = %(company)s
        AND IFNULL(pr.per_billed, 0) < 100
    """

    if from_date:
        conditions += " AND pr.posting_date >= %(from_date)s"
    if to_date:
        conditions += " AND pr.posting_date <= %(to_date)s"

    return frappe.db.sql(
        f"""
        SELECT
            pr.name,
            pr.posting_date,
            pr.grand_total,
            ROUND(
                pr.grand_total * (100 - IFNULL(pr.per_billed, 0)) / 100,
                3
            ) AS outstanding_amount
        FROM `tabPurchase Receipt` pr
        WHERE {conditions}
        HAVING outstanding_amount > %(min_outstanding)s
        ORDER BY pr.posting_date ASC
        """,
        {
            "supplier": supplier,
            "company": company,
            "from_date": from_date,
            "to_date": to_date,
            "min_outstanding": min_outstanding or 0,
        },
        as_dict=True,
    )


import frappe

@frappe.whitelist()
def get_item_purchase_and_stock(item_code, warehouse=None):
    """
    Returns:
      {
        "last_purchase_rate": <float>,  # from Item.last_purchase_rate
        "stock_in_hand": <float>        # from Bin.actual_qty
      }
    """

    # -----------------------
    # 1️⃣ LAST PURCHASE RATE (from Item)
    # -----------------------
    last_rate = frappe.db.get_value("Item", item_code, "last_purchase_rate") or 0

    # -----------------------
    # 2️⃣ STOCK IN HAND (from Bin)
    # -----------------------
    if warehouse:
        stock_qty = frappe.db.get_value(
            "Bin",
            {"item_code": item_code, "warehouse": warehouse},
            "actual_qty",
        ) or 0
    else:
        stock_qty = frappe.db.sql(
            """
            SELECT COALESCE(SUM(actual_qty), 0)
            FROM `tabBin`
            WHERE item_code = %s
            """,
            (item_code,),
        )[0][0] or 0

    return {
        "last_purchase_rate": float(last_rate),
        "stock_in_hand": float(stock_qty),
    }

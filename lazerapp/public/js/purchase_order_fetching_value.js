// Trigger when Item Code or Warehouse changes in Purchase Order Item table
frappe.ui.form.on('Purchase Order Item', {
    item_code(frm, cdt, cdn) {
        fetch_last_po_rate_and_stock(frm, cdt, cdn);
    },
    warehouse(frm, cdt, cdn) {
        fetch_last_po_rate_and_stock(frm, cdt, cdn);
    }
});

// Function to fetch last Purchase Order rate & stock from server
async function fetch_last_po_rate_and_stock(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.item_code) return;

    console.log("🔍 Fetching details for:", row.item_code, "Warehouse:", row.warehouse);

    frappe.call({
        method: "lazerapp.api.get_item_purchase_and_stock", // ✅ Python function path
        args: {
            item_code: row.item_code,
            warehouse: row.warehouse,
            company: frm.doc.company
        },
        callback: function(r) {
            console.log("✅ Response:", r);
            if (!r.message) {
                frappe.msgprint("No purchase history found for this item.");
                return;
            }

            const info = r.message;

            // ✅ Update the custom fields with fetched data
            frappe.model.set_value(cdt, cdn, "custom_last_purchase_rate", info.last_purchase_rate);
            frappe.model.set_value(cdt, cdn, "custom_stock_in_hand", info.stock_in_hand);

            // Optional: also set the rate field directly if you want it to match
            if (!row.rate || row.rate === 0) {
                frappe.model.set_value(cdt, cdn, "rate", info.last_purchase_rate);
            }

            frm.refresh_fields();
        },
        error: function(err) {
            console.error("❌ frappe.call failed:", err);
            frappe.msgprint("Failed to fetch last purchase rate. Check console for details.");
        }
    });
}

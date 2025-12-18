frappe.ui.form.on("Payment Entry Reference", {
    reference_name(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.reference_doctype === "Purchase Invoice" && row.reference_name) {
            frappe.db.get_value(
                "Purchase Invoice",
                row.reference_name,
                ["bill_no", "custom_grn_nos"],
                (r) => {
                    if (!r) return;

                    frappe.model.set_value(cdt, cdn,
                        "custom_supplier_invoice_number",
                        r.bill_no
                    );

                    frappe.model.set_value(cdt, cdn,
                        "custom_grn_nos",
                        r.custom_grn_nos
                    );
                }
            );
        }
    }
});


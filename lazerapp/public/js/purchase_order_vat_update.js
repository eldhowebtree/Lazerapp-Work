frappe.ui.form.on("Purchase Order", {
    validate(frm) {
        calculate_item_vat(frm);
    },
    taxes_and_charges_added(frm) {
        calculate_item_vat(frm);
    },
    taxes(frm) {
        calculate_item_vat(frm);
    }
});

frappe.ui.form.on("Purchase Order Item", {
    item_code(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            // Fetch custom_tax_rate from Item master automatically
            frappe.db.get_value("Item", row.item_code, "custom_tax_rate", (r) => {
                if (r && r.custom_tax_rate !== undefined) {
                    frappe.model.set_value(cdt, cdn, "custom_tax_rate", r.custom_tax_rate);
                    calculate_item_vat(frm);
                }
            });
        }
    },
    rate(frm, cdt, cdn) {
        calculate_item_vat(frm);
    },
    qty(frm, cdt, cdn) {
        calculate_item_vat(frm);
    },
    custom_tax_rate(frm, cdt, cdn) {
        calculate_item_vat(frm);
    }
});

function calculate_item_vat(frm) {
    if (!frm.doc.items || frm.doc.items.length === 0) return;

    frm.doc.items.forEach(row => {
        let rate = flt(row.rate);
        let qty = flt(row.qty);
        let tax_rate = flt(row.custom_tax_rate);
        let vat_amount = 0;
        let total_with_vat = 0;

        // ✅ VAT based on (rate × qty)
        if (tax_rate > 0) {
            vat_amount = (rate * qty * tax_rate) / 100;
        }

        // Set custom VAT
        frappe.model.set_value(row.doctype, row.name, "custom_vat_bd", vat_amount);

        // Total including VAT
        total_with_vat = (rate * qty) + vat_amount;
        frappe.model.set_value(row.doctype, row.name, "custom_total_with_vat", total_with_vat);
    });

    frm.refresh_field("items");
}

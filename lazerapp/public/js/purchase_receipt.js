frappe.ui.form.on("Purchase Receipt", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button("Make GRN Payment", () => {
                frappe.new_doc("GRN Payment", {
                    supplier: frm.doc.supplier,
                    company: frm.doc.company,
                    purchase_receipt: frm.doc.name,
                    amount: frm.doc.grand_total
                });
            }).addClass("btn-success");
        }
    }
});



/********************************
 * FINAL ITEM CALCULATION (CORRECT)
 ********************************/
frappe.ui.form.on('Purchase Receipt Item', {
    custom_quantity(frm, cdt, cdn) {
        calculate_item(cdt, cdn, frm);
    },
    rate(frm, cdt, cdn) {
        calculate_item(cdt, cdn, frm);
    },
    custom_vat_bd(frm, cdt, cdn) {
        calculate_item(cdt, cdn, frm);
    }
});

function calculate_item(cdt, cdn, frm) {
    let row = locals[cdt][cdn];

    let qty = flt(row.custom_quantity);
    let rate = flt(row.rate);
    let vat = flt(row.custom_vat_bd);

    // ✅ FINAL FORMULA
    let amount = (rate * qty) + vat;

    frappe.model.set_value(cdt, cdn, 'amount', amount);

    calculate_totals(frm);
}

function calculate_totals(frm) {
    let total = 0;

    (frm.doc.items || []).forEach(row => {
        total += flt(row.amount);
    });

    frm.set_value('total', total);
    frm.set_value('grand_total', total);
    frm.set_value('base_grand_total', total);
}

// frappe.ui.form.on("Purchase Receipt", {
//     refresh(frm) {
//         if (frm.doc.docstatus === 1) {
//             frm.add_custom_button("Make GRN Payment", () => {
//                 frappe.new_doc("GRN Payment", {
//                     supplier: frm.doc.supplier,
//                     company: frm.doc.company,
//                     purchase_receipt: frm.doc.name,
//                     amount: frm.doc.grand_total
//                 });
//             }).addClass("btn-success");
//         }
//     }
// });



/********************************
 * FINAL ITEM CALCULATION (CORRECT)
 ********************************/
frappe.ui.form.on('Purchase Receipt Item', {
    custom_quantity(frm, cdt, cdn) {
        calculate_item(frm, cdt, cdn);
    },

    rate(frm, cdt, cdn) {
        calculate_item(frm, cdt, cdn);
    },

    custom_vat_bd(frm, cdt, cdn) {
        calculate_item(frm, cdt, cdn);
    }
});

function calculate_item(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    let qty = flt(row.custom_quantity);
    let rate = flt(row.rate);
    let vat = flt(row.custom_vat_bd);

    let amount = (qty * rate) + vat;

    frappe.model.set_value(cdt, cdn, "amount", amount);

    frm.refresh_field("items");

    // Let ERPNext recalculate all totals
    frm.trigger("calculate_taxes_and_totals");
}
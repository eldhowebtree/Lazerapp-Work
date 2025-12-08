frappe.ui.form.on('Purchase Receipt', {
    refresh(frm) {
        // Show the button only when the Purchase Receipt is submitted
        if (frm.doc.docstatus === 1) {

            // Avoid duplicate button
            frm.page.remove_inner_button(__('Make Payment'));

            // Add the custom button
            frm.add_custom_button(__('Make Payment'), function() {
                // Create new Payment Entry prefilled with Supplier details
                frappe.model.with_doctype('Payment Entry', function() {
                    let payment_entry = frappe.model.get_new_doc('Payment Entry');
                    
                    // Pre-fill fields from Purchase Receipt
                    payment_entry.payment_type = 'Pay';
                    payment_entry.party_type = 'Supplier';
                    payment_entry.party = frm.doc.supplier;
                    payment_entry.company = frm.doc.company;
                    payment_entry.mode_of_payment = ''; // optional
                    payment_entry.reference_no = frm.doc.name; // link to Purchase Receipt
                    payment_entry.reference_date = frappe.datetime.now_date();
                    payment_entry.references = [
                        {
                            reference_doctype: 'Purchase Receipt',
                            reference_name: frm.doc.name,
                            total_amount: frm.doc.grand_total,
                            outstanding_amount: frm.doc.grand_total,
                            allocated_amount: frm.doc.grand_total
                        }
                    ];

                    // Open the new Payment Entry form
                    frappe.set_route('Form', 'Payment Entry', payment_entry.name);
                });
            })
            .addClass('btn-primary')
            .css({'background-color': '#008CBA', 'color': 'white'});
        }
    }
});

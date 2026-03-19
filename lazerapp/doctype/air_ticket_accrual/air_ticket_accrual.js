// Copyright (c) 2026, eldho.mathew@webtreeonline.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Air Ticket Accrual', {

    refresh: function(frm) {

        frm.add_custom_button('Recalculate Loan', function() {

            let accrued = frm.doc.monthly_accrual * frm.doc.months_completed;
            let used_amount = frm.doc.used_amount || 0;

            let loan = used_amount > accrued ? used_amount - accrued : 0;

            frm.set_value('loan_amount', loan);

            frappe.msgprint("Loan Amount Recalculated");
        });
    }

});
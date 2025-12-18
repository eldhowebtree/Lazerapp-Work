frappe.ui.form.on("Expense Claim", {
    onload: function (frm) {
        // Set today's date only if field is empty
        if (!frm.doc.custom_date) {
            frm.set_value("custom_date", frappe.datetime.get_today());
        }
    }
});

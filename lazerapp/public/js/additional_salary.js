frappe.ui.form.on('Additional Salary', {
    refresh(frm) {
        if (frappe.user.has_role('Branch Admin')) {

            const allowed = ['Commission','OT Salary'];

            if (!allowed.includes(frm.doc.salary_component)) {
                frm.set_df_property('amount','read_only',1);
                frappe.msgprint('You can edit only Commission and OT Salary');
            }
        }
    }
});
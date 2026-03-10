frappe.ui.form.on('*', {
    refresh(frm) {
        // Avoid duplicates
        if (frm.custom_back_button_added) return;

        frm.add_custom_button(__('Back'), function() {
            frappe.set_route('desk'); // Go to Desk main menu
        }).addClass('btn-primary');

        frm.custom_back_button_added = true;
    }
});

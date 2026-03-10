frappe.ui.form.on("Employee Transfer", {
    refresh(frm) {
        frm.trigger("calculate_indemnity");
    },

    custom_basic_salary_take_home(frm) {
        frm.trigger("calculate_indemnity");
    },

    custom_date_of_joining(frm) {
        frm.trigger("calculate_indemnity");
    },

    transfer_date(frm) {
        frm.trigger("calculate_indemnity");
    },

    calculate_indemnity(frm) {
        const salary = flt(frm.doc.custom_basic_salary_take_home);
        const doj = frm.doc.custom_date_of_joining ? frappe.datetime.str_to_obj(frm.doc.custom_date_of_joining) : null;
        const dot = frm.doc.transfer_date ? frappe.datetime.str_to_obj(frm.doc.transfer_date) : null;

        if (!salary || !doj || !dot) {
            frm.set_value("custom_total_years_of_service", 0);
            frm.set_value("custom_indemnity_type", "");
            frm.set_value("custom_calculated_indemnity", 0);
            return;
        }

        const total_days = frappe.datetime.get_diff(dot, doj);
        const years = Math.max(0, Math.floor(total_days / 365));
        frm.set_value("custom_total_years_of_service", years);

        let indemnity = 0;
        let type = "";

        if (years <= 3) {
            indemnity = (salary / 30) * 15 * years;
            type = "15 Days Salary / Year";
        } else {
            indemnity = salary * years;
            type = "1 Month Salary / Year";
        }

        frm.set_value("custom_indemnity_type", type);
        frm.set_value("custom_calculated_indemnity", indemnity);
        frm.refresh_fields([
            "custom_total_years_of_service",
            "custom_indemnity_type",
            "custom_calculated_indemnity"
        ]);
    },
});

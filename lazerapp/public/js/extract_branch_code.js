frappe.ui.form.on(cur_frm.doctype, {
    company(frm) {
        frm.trigger("update_branch_code");
    },

    refresh(frm) {
        frm.trigger("update_branch_code");
    },

    validate(frm) {
        frm.trigger("update_branch_code");
    },

    update_branch_code(frm) {
        // Run only if both company and custom_branch_code exist
        if (!frm.fields_dict.custom_branch_code) {
            console.warn(`[BranchCode] ${frm.doctype}: custom_branch_code field not found`);
            return;
        }

        if (frm.doc.company) {
            let company_name = frm.doc.company.trim();
            // Extract last number from company name (e.g., LAZER RIFFA BRANCH-4 → 4)
            let match = company_name.match(/(\d+)$/);
            let branch_number = match ? match[1] : "";

            frm.set_value("custom_branch_code", branch_number);

            console.log(`[BranchCode] ${frm.doctype} → ${branch_number}`);
        } else {
            // Clear if no company selected
            frm.set_value("custom_branch_code", "");
        }
    },
});

// Copyright (c) 2025, eldho.mathew@webtreeonline.com and contributors
// For license information, please see license.txt


frappe.ui.form.on("GRN Payment", {

    refresh(frm) {
        if (frm.doc.docstatus !== 0) return;

        // Prevent duplicate button
        frm.page.remove_inner_button(__("Get GRN Orders"), __("Actions"));

        frm.add_custom_button(
            __("Get GRN Orders"),
            () => open_grn_filter_dialog(frm),
            __("Actions")
        ).addClass("btn-primary");

        frm.trigger("update_branch_code");
    },

    custom_company(frm) {
        frm.trigger("update_branch_code");
    },

    validate(frm) {
        frm.trigger("update_branch_code");
    },

    update_branch_code(frm) {

        // Safety check
        if (!frm.fields_dict.custom_branch_code) {
            console.warn("[BranchCode] custom_branch_code field not found");
            return;
        }

        if (!frm.doc.custom_company) {
            frm.set_value("custom_branch_code", "");
            return;
        }

        let company_name = frm.doc.custom_company.trim();

        // Extract last number (e.g. BRANCH-4 → 4)
        let match = company_name.match(/(\d+)$/);
        let branch_number = match ? match[1] : "";

        frm.set_value("custom_branch_code", branch_number);

        console.log(`[BranchCode] Set to ${branch_number}`);
    }
});


// -------------------------------
// GRN FETCHING LOGIC
// -------------------------------

function open_grn_filter_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("Get GRN Orders"),
        size: "large",
        fields: [
            {
                fieldtype: "Date",
                fieldname: "from_date",
                label: "From Posting Date"
            },
            {
                fieldtype: "Date",
                fieldname: "to_date",
                label: "To Posting Date",
                default: frappe.datetime.get_today()
            },
            {
                fieldtype: "Float",
                fieldname: "min_outstanding",
                label: "Outstanding Amount >",
                default: 0
            }
        ],
        primary_action_label: __("Get GRN Orders"),
        primary_action(values) {
            dialog.hide();
            fetch_outstanding_grns(frm, values);
        }
    });

    dialog.show();
}

function fetch_outstanding_grns(frm, filters) {

    if (!frm.doc.supplier || !frm.doc.custom_company) {
        frappe.msgprint(__("Please select Supplier and Company first"));
        return;
    }

    frappe.call({
        method: "lazerapp.lazerapp.doctype.grn_payment.grn_payment.get_outstanding_grn_orders",
        args: {
            supplier: frm.doc.supplier,
            company: frm.doc.custom_company,
            from_date: filters.from_date || null,
            to_date: filters.to_date || null,
            min_outstanding: filters.min_outstanding || 0
        },
        callback(r) {
            if (!r.message || !r.message.length) {
                frappe.msgprint(__("No outstanding GRNs found"));
                return;
            }

            let grn = r.message[0];

            frm.set_value("custom_goods_received_note", grn.name);
            frm.set_value("custom_amount", grn.outstanding_amount);

            frappe.show_alert({
                message: __("GRN {0} loaded", [grn.name]),
                indicator: "green"
            });
        }
    });
}

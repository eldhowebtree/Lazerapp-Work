frappe.ui.form.on("Material Request", {
    material_request_type(frm) {
        frm.trigger("update_title_based_on_purpose");
    },

    supplier(frm) {
        frm.trigger("update_title_based_on_purpose");
    },

    update_title_based_on_purpose(frm) {
        let purpose = frm.doc.material_request_type || "";
        let supplier = frm.doc.supplier || "";
        let item_name = "";

        // Get first item name if available
        if (frm.doc.items && frm.doc.items.length > 0) {
            item_name = frm.doc.items[0].item_name || "";
        }

        let new_title = "";

        if (purpose === "Purchase") {
            new_title = supplier
                ? `Purchase Request for ${supplier}`
                : "Purchase Request";
        } 
        else if (purpose === "Material Transfer") {
            new_title = item_name
                ? `Material Transfer Request for ${item_name}`
                : "Material Transfer Request";
        } 
        else if (purpose === "Material Issue") {
            new_title = item_name
                ? `Material Issue Request for ${item_name}`
                : "Material Issue Request";
        }

        if (new_title) {
            frm.set_value("title", new_title);
            console.log(`✅ Title updated to: ${new_title}`);
        }
    }
});

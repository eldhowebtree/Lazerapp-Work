frappe.ui.form.on('Material Request', {
    refresh: function (frm) {

        // 🔥 Remove ONLY your custom button group (safe)
        frm.page.wrapper
            .find('.btn-group:contains("Fetch Items From Item Group")')
            .remove();

        // Add CSS for blinking animation once
        if (!document.getElementById('blink-animation-style')) {
            let style = document.createElement('style');
            style.id = 'blink-animation-style';
            style.innerHTML = `
                @keyframes blink-green {
                    0%, 100% { 
                        background-color: #28a745; 
                        border-color: #28a745;
                        opacity: 1;
                    }
                    50% { 
                        background-color: #20c997; 
                        border-color: #20c997;
                        opacity: 0.7;
                    }
                }
                .btn-blink-green {
                    background-color: #28a745 !important;
                    border-color: #28a745 !important;
                    color: white !important;
                    animation: blink-green 1.5s ease-in-out infinite;
                }
                .btn-blink-green:hover {
                    background-color: #218838 !important;
                    border-color: #1e7e34 !important;
                }
            `;
            document.head.appendChild(style);
        }

        // Fetch all Item Groups except "Services" and "Carwash"
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Group",
                fields: ["name"],
                filters: [
                    ["name", "not in", ["Services", "Carwash"]]  // 👈 exclude here
                ],
                order_by: "name asc"
            },
            callback: function (res) {
                if (res.message && res.message.length > 0) {
                    const groups = res.message.map(d => d.name);
                    groups.push("All Item Groups"); // Add universal option

                    // Create dynamic buttons under one main group
                    groups.forEach(group => {
                        frm.add_custom_button(group, function () {
                            open_item_selection_dialog(frm, group);
                        }, __('Fetch Items From Item Group'));
                    });

                    // Add blinking green style to parent button
                    setTimeout(function () {
                        let parent_button = frm.page.wrapper.find('.btn-group:contains("Fetch Items From Item Group") > .btn');
                        if (parent_button.length > 0) {
                            parent_button.addClass('btn-blink-green');
                        }
                    }, 300);
                }
            }
        });
    }
});


function open_item_selection_dialog(frm, group) {
    let limit = 20; // default items per page
    let start = 0;
    let all_items = [];
    let total_count = 0;
    let d;

    const fetch_items = () => {
        // 👇 exclude Services and Carwash items in both All and filtered modes
        let filters = {
            "disabled": 0,
            "is_purchase_item": 1,
            "item_group": ["not in", ["Services", "Carwash"]]
        };

        if (group !== "All Item Groups") {
            filters["item_group"] = ["=", group];
        }

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item",
                filters: filters,
                fields: ["name", "item_name", "description", "stock_uom", "item_group", "standard_rate"],
                limit_start: start,
                limit_page_length: limit,
                order_by: "item_name asc"
            },
            callback: function (r) {
                if (!r.message || r.message.length === 0) {
                    if (start === 0) frappe.msgprint(`No active purchase items found for ${group}`);
                    return;
                }
                all_items = r.message;
                refresh_table();
            }
        });
    };

    const refresh_table = () => {
        const with_serial = (items) => {
            return items.map((item, index) => ({
                sl_no: start + index + 1,
                item_code: item.name,
                item_name: item.item_name,
                description: item.description,
                stock_uom: item.stock_uom,
                item_group: item.item_group,
                select: 0
            }));
        };

        let table_field = d.fields_dict.items_table;
        table_field.df.data = with_serial(all_items);
        table_field.refresh();

        // update page info
        d.fields_dict.page_info.$wrapper.text(
            `Showing ${start + 1} - ${start + all_items.length} of ${total_count} items`
        );
    };

    // Get total count excluding Services & Carwash
    frappe.call({
        method: "frappe.client.get_count",
        args: {
            doctype: "Item",
            filters: group === "All Item Groups" ? {
                "disabled": 0,
                "is_purchase_item": 1,
                "item_group": ["not in", ["Services", "Carwash"]]
            } : {
                "item_group": group,
                "disabled": 0,
                "is_purchase_item": 1
            }
        },
        callback: function (res) {
            total_count = res.message;
            build_dialog();
            fetch_items();
        }
    });

    const build_dialog = () => {
        d = new frappe.ui.Dialog({
            title: `Select Items from ${group}`,
            size: "extra-large",
            fields: [
                {
                    fieldname: "search_box",
                    fieldtype: "Data",
                    label: "Search Item",
                    onchange: function () {
                        let search_term = (this.value || "").toLowerCase();
                        let filtered = all_items.filter(item =>
                            item.item_name.toLowerCase().includes(search_term) ||
                            item.name.toLowerCase().includes(search_term) ||
                            (item.description && item.description.toLowerCase().includes(search_term))
                        );

                        let table_field = d.fields_dict.items_table;
                        table_field.df.data = filtered.map((item, index) => ({
                            sl_no: start + index + 1,
                            item_code: item.name,
                            item_name: item.item_name,
                            description: item.description,
                            stock_uom: item.stock_uom,
                            item_group: item.item_group,
                            select: 0
                        }));
                        table_field.refresh();
                    }
                },
                {
                    fieldname: "limit_selector",
                    fieldtype: "Select",
                    label: "Items per page",
                    options: ["20", "100", "500", "1000"],
                    default: "20",
                    onchange: function () {
                        limit = parseInt(this.value);
                        start = 0;
                        fetch_items();
                    }
                },
                {
                    fieldname: "pagination_controls",
                    fieldtype: "Section Break"
                },
                {
                    fieldname: "prev_btn",
                    fieldtype: "Button",
                    label: "Previous",
                    click: function () {
                        if (start > 0) {
                            start -= limit;
                            if (start < 0) start = 0;
                            fetch_items();
                        }
                    }
                },
                {
                    fieldname: "next_btn",
                    fieldtype: "Button",
                    label: "Next",
                    click: function () {
                        if (start + limit < total_count) {
                            start += limit;
                            fetch_items();
                        }
                    }
                },
                {
                    fieldname: "page_info",
                    fieldtype: "HTML"
                },
                {
                    fieldname: "items_table",
                    fieldtype: "Table",
                    label: "Items",
                    cannot_add_rows: true,
                    in_place_edit: false,
                    show_toolbar: false,
                    reqd: 1,
                    data: [],
                    get_data: function () {
                        return this.df.data;
                    },
                    fields: [
                        { fieldtype: "Int", fieldname: "sl_no", label: "Sl No", in_list_view: 1, width: "6%", read_only: 1 },
                        { fieldtype: "Check", fieldname: "select", label: "Select", in_list_view: 1, width: "5%" },
                        { fieldtype: "Data", fieldname: "item_code", label: "Item Code", in_list_view: 1, read_only: 1 },
                        { fieldtype: "Data", fieldname: "item_name", label: "Item Name", in_list_view: 1, read_only: 1 },
                        { fieldtype: "Data", fieldname: "description", label: "Description", in_list_view: 1, read_only: 1 },
                        { fieldtype: "Data", fieldname: "stock_uom", label: "UOM", in_list_view: 1, read_only: 1 },
                        { fieldtype: "Data", fieldname: "item_group", label: "Group", in_list_view: 1, read_only: 1 },
                    ]
                }
            ],
            primary_action_label: "Add Selected Items",
            primary_action(values) {
                const selected_items = d.fields_dict.items_table.grid.data.filter(i => i.select);
                if (!selected_items.length) {
                    frappe.msgprint("Please select at least one item.");
                    return;
                }

                const existing = frm.doc.items.map(i => i.item_code);
                let added_count = 0;

                selected_items.forEach(item => {
                    if (!existing.includes(item.item_code)) {
                        let row = frm.add_child("items");
                        row.item_code = item.item_code;
                        row.item_name = item.item_name;
                        row.description = item.description;
                        row.uom = item.stock_uom;

                        frm.script_manager.trigger("item_code", row);
                        added_count++;
                    }
                });

                frappe.msgprint(`${added_count} new item(s) added from ${group}`);
                frm.refresh_field("items");
                d.hide();
            }
        });

        d.show();

        // Hide index column
        setTimeout(() => {
            d.$wrapper.find('.row-index').hide();
            d.$wrapper.find('.grid-heading-row .row-index').hide();
            d.$wrapper.find('.grid-body').css('margin-left', '0px');
        }, 300);
    };
}




frappe.ui.form.on('Material Request', {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {

            // Remove duplicate buttons
            frm.page.wrapper.find('.btn-group:contains("Create Purchase Order")').remove();

            // Add custom button
            frm.add_custom_button(__('Create Purchase Order'), function () {

                frappe.model.open_mapped_doc({
                    method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order",
                    frm: frm
                });

            }).addClass('btn-primary');
        }
    }
});

frappe.ui.form.on('Material Request', {
    refresh(frm) {
        // Remove default button
        frm.remove_custom_button('Purchase Order', 'Create');

        // Add custom direct-create button
        frm.add_custom_button(__('Purchase Order'), function() {
            if (!frm.doc.name) {
                frappe.msgprint(__('Please save the Material Request first.'));
                return;
            }

            frappe.call({
                method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order",
                args: {
                    source_name: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Creating Purchase Order..."),
                callback: function(r) {
                    if (!r.exc && r.message) {
                        frappe.model.sync(r.message);
                        frappe.set_route("Form", r.message.doctype, r.message.name);
                    }
                }
            });
        }, __("Create"));
    }
});









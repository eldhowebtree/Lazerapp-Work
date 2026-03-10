// Copyright (c) 2025, eldho.mathew@webtreeonline.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Indemnity Settlement", {
  refresh(frm) {
    if (!frm.is_new()) {
      frm.add_custom_button("Recalculate", () => {
        frm.save();
      }).addClass("btn-primary");
    }
  }
});


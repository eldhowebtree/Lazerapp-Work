frappe.ui.form.on("Employee", {
    date_of_joining(frm) {
        calculate_family_ticket_dates(frm);
    },
    custom_family_ticket_eligibility_year(frm) {
        calculate_family_ticket_dates(frm);
    }
});

function calculate_family_ticket_dates(frm) {
    if (
        !frm.doc.date_of_joining ||
        !frm.doc.custom_family_ticket_eligibility_year
    ) {
        return;
    }

    let years = parseInt(frm.doc.custom_family_ticket_eligibility_year, 10);
    if (isNaN(years)) return;

    // 1️⃣ First eligible date
    let eligible_from = frappe.datetime.add_months(
        frm.doc.date_of_joining,
        years * 12
    );

    frm.set_value("custom_family_ticket_eligible_from", eligible_from);

    // 2️⃣ Next eligible cycle
    let next_eligible = frappe.datetime.add_months(
        eligible_from,
        years * 12
    );

    frm.set_value("custom_next_year_of_eligible", next_eligible);
}

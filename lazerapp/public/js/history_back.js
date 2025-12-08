(function () {
  const BTN_ID = 'lazerapp-history-back-btn';

  function create_back_button() {
    if (document.getElementById(BTN_ID)) return;

    // don't show on login/setup
    const route = frappe.get_route ? frappe.get_route() : [];
    if (route && (route[0] === 'login' || route[0] === 'setup-wizard')) return;

    const btn = document.createElement('button');
    btn.id = BTN_ID;
    btn.type = 'button';
    btn.className = 'btn btn-default btn-shadow lazerapp-back-btn';
    btn.setAttribute('title', __('Back'));

    // icon + text (icon fallback-safe)
    btn.innerHTML = `
      <span class="icon icon-arrow-left" style="margin-right:6px;"></span>
      <span>${__('Back')}</span>
    `;

    btn.onclick = () => {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        // fallback to Desk home if no history
        frappe.set_route('desk');
      }
    };

    document.body.appendChild(btn);
  }

  function ensure_button() {
    // Delay slightly to avoid DOM race on route changes
    setTimeout(create_back_button, 50);
  }

  // First load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensure_button);
  } else {
    ensure_button();
  }

  // Recreate on every route change (forms, lists, reports, pages)
  if (frappe.router && frappe.router.on) {
    frappe.router.on('change', ensure_button);
  } else {
    // fallback for older router
    $(document).on('page-change', ensure_button);
  }

  // Optional: keyboard shortcut Alt + ← (native), add Alt+B
  document.addEventListener('keydown', (e) => {
    if ((e.altKey || e.metaKey) && (e.key === 'b' || e.key === 'B')) {
      e.preventDefault();
      btn = document.getElementById(BTN_ID);
      if (btn) btn.click();
    }
  });
})();

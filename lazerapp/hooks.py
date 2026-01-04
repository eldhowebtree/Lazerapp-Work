app_name = "lazerapp"
app_title = "Lazerapp"
app_publisher = "eldho.mathew@webtreeonline.com"
app_description = "lazerapp"
app_email = "eldho.mathew@webtreeonline.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "lazerapp",
# 		"logo": "/assets/lazerapp/logo.png",
# 		"title": "Lazerapp",
# 		"route": "/lazerapp",
# 		"has_permission": "lazerapp.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lazerapp/css/lazerapp.css"
# app_include_js = "/assets/lazerapp/js/lazerapp.js"

# include js, css files in header of web template
# web_include_css = "/assets/lazerapp/css/lazerapp.css"
# web_include_js = "/assets/lazerapp/js/lazerapp.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lazerapp/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lazerapp/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lazerapp.utils.jinja_methods",
# 	"filters": "lazerapp.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lazerapp.install.before_install"
# after_install = "lazerapp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lazerapp.uninstall.before_uninstall"
# after_uninstall = "lazerapp.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lazerapp.utils.before_app_install"
# after_app_install = "lazerapp.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lazerapp.utils.before_app_uninstall"
# after_app_uninstall = "lazerapp.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lazerapp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"lazerapp.tasks.all"
# 	],
# 	"daily": [
# 		"lazerapp.tasks.daily"
# 	],
# 	"hourly": [
# 		"lazerapp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lazerapp.tasks.weekly"
# 	],
# 	"monthly": [
# 		"lazerapp.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "lazerapp.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lazerapp.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lazerapp.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lazerapp.utils.before_request"]
# after_request = ["lazerapp.utils.after_request"]

# Job Events
# ----------
# before_job = ["lazerapp.utils.before_job"]
# after_job = ["lazerapp.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lazerapp.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


doctype_js = {
    "Material Request": [
        "public/js/material_request_item_group.js",
        "public/js/extract_branch_code.js",
        "public/js/material_request_update_title.js",
        "public/js/history_back.js"
    ],

    "Purchase Order": [
        "public/js/purchase_order_item_group.js",
        "public/js/extract_branch_code.js",
        "public/js/purchase_order_vat_update.js"
    ],

    "Purchase Receipt": [
        "public/js/purchase_receipt.js",
        "public/js/extract_branch_code.js"
    ],

    "Payment Entry": [
        "public/js/payment_entry.js",
        "public/js/extract_branch_code.js"
    ],

    "Employee Transfer": [
        "public/js/extract_branch_code.js"
    ],

    "Sales Invoice": [
        "public/js/extract_branch_code.js"
    ],

    "Purchase Invoice": [
        "public/js/extract_branch_code.js"
    ],

    "Employee": [
        "public/js/extract_branch_code.js"
    ],

    "Expense Claim": [
        "public/js/expense_claim.js",
        "public/js/extract_branch_code.js"
    ],
    "Leave Application":[

        "public/js/extract_branch_code.js",
    ]

    


}


fixtures = [
    {
        "doctype": "Property Setter",
        "filters": [
            ["doc_type", "=", "Material Request"],
            ["field_name", "=", "material_request_type"]
        ]
    }
]

fixtures = ["Custom Field"]





# doc_events = {
#     "Employee Transfer": {
#         "before_save": "lazerapp.extend.employee_transfer_override.calculate_employee_indemnity"
#     }
# }

app_include_js = [
    "/assets/lazerapp/js/history_back.js"
]




fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Lazer App"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Lazer App"]]},
]
fixtures = ["Custom Field", "Property Setter"]

app_include_js = ["lazerapp/public/js/history_back.js"]
app_include_css = ["lazerapp/public/css/history_back.css"]


override_doctype_class = {
    "Purchase Order": "lazerapp.doctype_overrides.purchase_order_override.CustomPurchaseOrder",
    "Purchase Receipt": "lazerapp.doctype_overrides.purchase_receipt.CustomPurchaseReceipt",
    # "Payment Entry": "lazerapp.doctype_overrides.payment_entry.PaymentEntry",
    "Purchase Invoice": "lazerapp.doctype_overrides.purchase_invoice.CustomPurchaseInvoice",
    "Leave Application": "lazerapp.doctype_overrides.leave_application.CustomLeaveApplication",
}



doc_events = {
    "Purchase Order": {
        "before_save": "lazerapp.doctype_overrides.bahrain_rounding.apply_bahrain_rounding"
    },
    "Purchase Invoice": {
        "before_save": "lazerapp.doctype_overrides.bahrain_rounding.apply_bahrain_rounding"
    },
    "Sales Invoice": {
        "before_save": "lazerapp.doctype_overrides.bahrain_rounding.apply_bahrain_rounding"
    },
    "Sales Order": {
        "before_save": "lazerapp.doctype_overrides.bahrain_rounding.apply_bahrain_rounding"
    },
    "Quotation": {
        "before_save": "lazerapp.doctype_overrides.bahrain_rounding.apply_bahrain_rounding"
    },

    
   "Compensatory Leave Request": {
        "validate": "lazerapp.doctype_overrides.compensatory_leave_request.validate"
    }


   
}





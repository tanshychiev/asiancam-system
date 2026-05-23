from django.urls import path

from . import views, report_pages
from .report_exports import export_accounting_report


urlpatterns = [
    # =====================================================
    # Chart of Accounts
    # =====================================================
    path("chart-of-accounts/", views.chart_of_accounts, name="chart_of_accounts"),
    path("chart-of-accounts/setup-sample/", views.setup_sample_coa, name="setup_sample_coa"),
    path("chart-of-accounts/new/", views.account_create, name="account_create"),
    path("chart-of-accounts/<int:account_id>/edit/", views.account_edit, name="account_edit"),
    path("chart-of-accounts/<int:account_id>/toggle/", views.account_toggle_active, name="account_toggle_active"),

    # =====================================================
    # Journal / Accounting Data
    # =====================================================
    path("journals/", views.journal_list, name="journal_list"),
    path("journals/new/", views.journal_create, name="journal_create"),
    path("journals/<int:entry_id>/", views.journal_detail, name="journal_detail"),
    path("journals/<int:entry_id>/edit/", views.journal_edit, name="journal_edit"),
    path("journals/<int:entry_id>/delete/", views.journal_delete, name="journal_delete"),

    # Dashboard shortcuts
    path("data/", views.accounting_data_list, name="accounting_data_list"),
    path("data/new/", views.accounting_data_create, name="accounting_data_create"),

    # =====================================================
    # Journal Excel Import
    # =====================================================
    path("import-excel/", views.accounting_import_excel, name="accounting_import_excel"),
    path("import-excel/sample/", views.download_journal_import_sample, name="download_journal_import_sample"),

    # =====================================================
    # Bulk Update - 3 Real Functions
    # =====================================================
    path("bulk-update/", views.bulk_update_items, name="bulk_update_menu"),
    path("bulk-update/vendors/", views.bulk_update_vendors, name="bulk_update_vendors"),
    path("bulk-update/items/", views.bulk_update_items, name="bulk_update_items"),
    path("bulk-update/customers/", views.bulk_update_customers, name="bulk_update_customers"),

    path("bulk-update/sample/", views.download_bulk_update_sample, name="download_bulk_update_sample"),
    path("bulk-update/upload/", views.upload_bulk_update, name="upload_bulk_update"),
    path("bulk-update/report/<int:log_id>/", views.bulk_update_report, name="bulk_update_report"),

    # =====================================================
    # Reports - 1 report = 1 page
    # =====================================================
    path("reports/", report_pages.report_home, name="accounting_reports"),
    path("reports/profit-loss-by-month/", report_pages.report_profit_loss_by_month, name="report_profit_loss_by_month"),
    path("reports/general-ledger/", report_pages.report_general_ledger, name="report_general_ledger"),
    path("reports/ap-aging/", report_pages.report_ap_aging, name="report_ap_aging"),
    path("reports/ar-aging/", report_pages.report_ar_aging, name="report_ar_aging"),
    path("reports/balance-sheet/", report_pages.report_balance_sheet, name="report_balance_sheet"),
    path("reports/profit-loss-standard/", report_pages.report_profit_loss_standard, name="report_profit_loss_standard"),
    path("reports/journal-report/", report_pages.report_journal_report, name="report_journal_report"),
    path("reports/trial-balance/", report_pages.report_trial_balance, name="report_trial_balance"),
    path("reports/cash-flow/", report_pages.report_cash_flow, name="report_cash_flow"),

    path("reports/ledger/<int:account_id>/", views.report_ledger_detail, name="report_ledger_detail"),
    path("reports/export/<str:report_slug>/", export_accounting_report, name="accounting_report_export"),

    # =====================================================
    # Menu pages
    # =====================================================
    path("report-mapping/", views.report_mapping, name="report_mapping"),
    path("banking/", views.banking_menu, name="banking_menu"),
    path("bank-deposit/", views.bank_deposit, name="bank_deposit"),
    path("landed-cost/", views.landed_cost_allocation, name="landed_cost_allocation"),
    path("find-transaction/", views.find_transaction, name="find_transaction"),
    path("batch-transaction/", views.batch_transaction, name="batch_transaction"),
    path("import/", views.import_menu, name="import_menu"),
]

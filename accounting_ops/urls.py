from django.urls import path

from . import views
from .models import ImportHistory

urlpatterns = [
    # =========================
    # Bank
    # =========================
    path("bank-accounts/", views.bank_account_list, name="ops_bank_account_list"),
    path("bank-accounts/new/", views.bank_account_create, name="ops_bank_account_create"),

    path("bank-deposits/", views.bank_deposit_list, name="ops_bank_deposit_list"),
    path("bank-deposits/new/", views.bank_deposit_create, name="ops_bank_deposit_create"),

    path("bank-rules/", views.bank_rule_list, name="ops_bank_rule_list"),
    path("bank-rules/new/", views.bank_rule_create, name="ops_bank_rule_create"),

    path("bank-reconciles/", views.bank_reconcile_list, name="ops_bank_reconcile_list"),
    path("bank-reconciles/new/", views.bank_reconcile_create, name="ops_bank_reconcile_create"),

    # =========================
    # Landed Cost
    # =========================
    path("landed-costs/", views.landed_cost_list, name="ops_landed_cost_list"),
    path("landed-costs/new/", views.landed_cost_create, name="ops_landed_cost_create"),

    # =========================
    # Search / Batch
    # =========================
    path("find-transaction/", views.find_transaction, name="ops_find_transaction"),
    path("batch-transaction/", views.batch_transaction, name="ops_batch_transaction"),

    # =========================
    # Import Pages - Master Data
    # =========================
    path(
        "import/chart-of-account/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_COA},
        name="ops_import_coa",
    ),
    path(
        "import/item/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_ITEM},
        name="ops_import_item",
    ),
    path(
        "import/vendor/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_VENDOR},
        name="ops_import_vendor",
    ),
    path(
        "import/customer/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_CUSTOMER},
        name="ops_import_customer",
    ),

    # =========================
    # Import Pages - Opening Balance
    # =========================
    path(
        "import/trial-balance/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_TRIAL_BALANCE},
        name="ops_import_trial_balance",
    ),
    path(
        "import/journal-opening/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_JOURNAL_OPENING},
        name="ops_import_journal_opening",
    ),
    path(
        "import/outstanding-ap/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_OUTSTANDING_AP},
        name="ops_import_outstanding_ap",
    ),
    path(
        "import/outstanding-ar/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_OUTSTANDING_AR},
        name="ops_import_outstanding_ar",
    ),

    # =========================
    # Import Pages - Stock / Transaction
    # =========================
    path(
        "import/stock-balance/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_STOCK_BALANCE},
        name="ops_import_stock_balance",
    ),
    path(
        "import/batch-transaction/",
        views.import_page,
        {"import_type": ImportHistory.TYPE_BATCH_TRANSACTION},
        name="ops_import_batch_transaction",
    ),

    # =========================
    # Download Sample Format
    # =========================
    path(
        "sample/<str:import_type>/",
        views.download_sample,
        name="ops_download_sample",
    ),
]

from django.urls import path

from . import views
from .models import VendorTransaction

urlpatterns = [
    path("", views.vendor_center, name="vendor_center"),
    path("print/", views.vendor_print, name="vendor_print"),
    path("new/", views.vendor_create, name="vendor_create"),
    path("<int:vendor_id>/edit/", views.vendor_edit, name="vendor_edit"),

    path(
        "export-excel/",
        views.vendor_export_excel,
        name="vendor_export_excel",
    ),

    path(
        "import-excel/",
        views.vendor_import_excel,
        name="vendor_import_excel",
    ),

    path(
        "import-excel/sample/",
        views.vendor_import_sample,
        name="vendor_import_sample",
    ),

    path(
        "purchase-bills/",
        views.purchase_bill_list,
        name="purchase_bill_list",
    ),
    path(
        "purchase-bills/new/",
        views.purchase_bill_create,
        name="purchase_bill_create",
    ),
    path(
        "purchase-bills/<int:bill_id>/",
        views.purchase_bill_detail,
        name="purchase_bill_detail",
    ),
    path(
        "purchase-bills/<int:bill_id>/edit/",
        views.purchase_bill_edit,
        name="purchase_bill_edit",
    ),
    path(
        "purchase-bills/<int:bill_id>/print/",
        views.purchase_bill_print,
        name="purchase_bill_print",
    ),

    path(
        "transactions/",
        views.vendor_transaction_list,
        name="vendor_transaction_list",
    ),
    path(
        "transactions/new/",
        views.vendor_transaction_create,
        name="vendor_transaction_create",
    ),
    path(
        "transactions/<int:transaction_id>/",
        views.vendor_transaction_detail,
        name="vendor_transaction_detail",
    ),
    path(
        "transactions/<int:transaction_id>/edit/",
        views.vendor_transaction_edit,
        name="vendor_transaction_edit",
    ),

    path(
        "purchase-order/new/",
        views.purchase_bill_create,
        name="purchase_order_create",
    ),
    path(
        "cash-expense/new/",
        views.vendor_payment_new,
        name="cash_expense_create",
    ),
    path(
        "payment/new/",
        views.vendor_payment_new,
        name="vendor_payment_create",
    ),
    path(
        "payment/<int:payment_id>/edit/",
        views.vendor_payment_edit,
        name="vendor_payment_edit",
    ),
    path(
        "payment/<int:payment_id>/print/",
        views.vendor_payment_print,
        name="vendor_payment_print",
    ),
]
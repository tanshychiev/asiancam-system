from django.urls import path

from . import views
from .models import VendorTransaction

urlpatterns = [
    path("", views.vendor_center, name="vendor_center"),
    path("new/", views.vendor_create, name="vendor_create"),
    path("<int:vendor_id>/edit/", views.vendor_edit, name="vendor_edit"),

    path("transactions/", views.vendor_transaction_list, name="vendor_transaction_list"),
    path("transactions/new/", views.vendor_transaction_create, name="vendor_transaction_create"),
    path("transactions/<int:transaction_id>/", views.vendor_transaction_detail, name="vendor_transaction_detail"),

    path(
        "purchase-order/new/",
        views.vendor_transaction_create,
        {"transaction_type": VendorTransaction.TYPE_PURCHASE_ORDER},
        name="purchase_order_create",
    ),
    path(
        "cash-expense/new/",
        views.vendor_transaction_create,
        {"transaction_type": VendorTransaction.TYPE_CASH_EXPENSE},
        name="cash_expense_create",
    ),
    path(
        "payment/new/",
        views.vendor_transaction_create,
        {"transaction_type": VendorTransaction.TYPE_VENDOR_PAYMENT},
        name="vendor_payment_create",
    ),
]
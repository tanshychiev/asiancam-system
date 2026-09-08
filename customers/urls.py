from django.urls import path

from . import views

urlpatterns = [
    path("customer-center/export/", views.customer_export_excel, name="customer_export_excel"),
    path("customer-center/import/", views.customer_import_excel, name="customer_import_excel"),
    path("customer-center/import/sample/", views.customer_import_sample, name="customer_import_sample"),
    path("customer-center/print/", views.customer_center_print, name="customer_center_print"),

    path("transactions/<int:transaction_id>/center-action/", views.customer_center_transaction_action, name="customer_center_transaction_action"),
    path("transactions/<int:transaction_id>/duplicate/", views.customer_transaction_duplicate, name="customer_transaction_duplicate"),
    path("invoices/<int:invoice_id>/center-action/", views.customer_center_invoice_action, name="customer_center_invoice_action"),
    path("invoices/<int:invoice_id>/duplicate/", views.customer_invoice_duplicate, name="customer_invoice_duplicate"),
    path("receipts/<int:receipt_id>/center-action/", views.customer_center_receipt_action, name="customer_center_receipt_action"),
    path("receipts/<int:receipt_id>/duplicate/", views.customer_receipt_duplicate, name="customer_receipt_duplicate"),

    path("invoice-list/", views.sales_invoice_list, name="customer_invoice_list"),

    # MAIN Sale Invoice screen — use the modern Sale Invoice view/template.
    path("invoice/new/", views.sales_invoice_create, name="customer_invoice_create"),

    # Keep the v2 URL as an alias so old bookmarks still work.
    path("invoice/new-v2/", views.sales_invoice_create, name="customer_invoice_create_v2"),

    # Keep the old generic CustomerTransaction invoice form only as a legacy URL.
    path("invoice/legacy/new/", views.invoice_create, name="customer_invoice_legacy_create"),

    path("sale-receipt/", lambda request: views.sales_invoice_list(request, views.SalesInvoice.TYPE_SALE_RECEIPT), name="sale_receipt_list"),
    path("sale-receipt/new/", lambda request: views.sales_invoice_create(request, views.SalesInvoice.TYPE_SALE_RECEIPT), name="sale_receipt_create"),
    path("customer-center/", views.customer_center, name="customer_center"),
    path("customer-center/new/", views.customer_create, name="customer_create"),
    path("customer-center/<int:customer_id>/edit/", views.customer_edit, name="customer_edit"),

    path("transaction-list/", views.customer_transaction_list, name="customer_transaction_list"),
    path("transactions/new/", views.customer_transaction_create, name="customer_transaction_create"),
    path("transactions/<int:transaction_id>/", views.customer_transaction_detail, name="customer_transaction_detail"),

    path("receive-payment/new/", views.customer_receipt_create, name="receive_payment_create"),

    path("quotation-list/", views.quotation_list, name="quotation_list"),
    path("quotation/new/", views.quotation_create, name="quotation_create"),

    path("sale-order-list/", views.sale_order_list, name="sale_order_list"),
    path("sale-order/new/", views.sale_order_create, name="sale_order_create"),

    path("customers-type/", views.customer_type_list, name="customer_type_list"),
    path("customers-type/new/", views.customer_type_create, name="customer_type_create"),

    path("sale-persons/", views.salesperson_list, name="salesperson_list"),
    path("sale-persons/new/", views.salesperson_create, name="salesperson_create"),

    path("price-levels/", views.price_level_list, name="price_level_list"),
    path("price-levels/new/", views.price_level_create, name="price_level_create"),

    path("regions/", views.region_list, name="region_list"),
    path("regions/new/", views.region_create, name="region_create"),

    path("documents/<str:document_type>/", views.sales_document_list, name="sales_document_list"),
    path("documents/<str:document_type>/new/", views.sales_document_create, name="sales_document_create"),
]
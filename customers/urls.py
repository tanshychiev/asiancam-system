from django.urls import path

from . import views

urlpatterns = [
    path("customer-center/", views.customer_center, name="customer_center"),
    path("customer-center/new/", views.customer_create, name="customer_create"),
    path("customer-center/<int:customer_id>/edit/", views.customer_edit, name="customer_edit"),

    path("transaction-list/", views.customer_transaction_list, name="customer_transaction_list"),
    path("transactions/new/", views.customer_transaction_create, name="customer_transaction_create"),
    path("transactions/<int:transaction_id>/", views.customer_transaction_detail, name="customer_transaction_detail"),

    path("invoice/new/", views.invoice_create, name="customer_invoice_create"),
    path("receive-payment/new/", views.receive_payment_create, name="receive_payment_create"),

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
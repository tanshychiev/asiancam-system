from django.urls import path

from . import views

urlpatterns = [
    path("items/", views.item_list, name="stock_item_list"),
    path("items/new/", views.item_create, name="stock_item_create"),
    path("items/<int:item_id>/edit/", views.item_edit, name="stock_item_edit"),

    path("item-groups/", views.item_group_list, name="stock_item_group_list"),
    path("item-groups/new/", views.item_group_create, name="stock_item_group_create"),

    path("item-brands/", views.item_brand_list, name="stock_item_brand_list"),
    path("item-brands/new/", views.item_brand_create, name="stock_item_brand_create"),

    path("unit-sets/", views.unit_set_list, name="stock_unit_set_list"),
    path("unit-sets/new/", views.unit_set_create, name="stock_unit_set_create"),

    path("warehouses/", views.warehouse_list, name="stock_warehouse_list"),
    path("warehouses/new/", views.warehouse_create, name="stock_warehouse_create"),

    path("stock-issues/", views.stock_issue_list, name="stock_issue_list"),
    path("stock-issues/new/", views.stock_issue_create, name="stock_issue_create"),

    path("stock-adjustments/", views.stock_adjustment_list, name="stock_adjustment_list"),
    path("stock-adjustments/new/", views.stock_adjustment_create, name="stock_adjustment_create"),

    path("stock-assemblies/", views.stock_assembly_list, name="stock_assembly_list"),
    path("stock-assemblies/new/", views.stock_assembly_create, name="stock_assembly_create"),

    path("stock-transfers/", views.stock_transfer_list, name="stock_transfer_list"),
    path("stock-transfers/new/", views.stock_transfer_create, name="stock_transfer_create"),
]
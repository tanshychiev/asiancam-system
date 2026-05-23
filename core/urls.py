from django.urls import path
from . import views

urlpatterns = [
    # Companies
    path("companies/", views.company_list, name="company_list"),
    path("companies/create/", views.company_create, name="company_create"),
    path("companies/assign-staff/", views.assign_staff, name="assign_staff"),
    path("companies/<int:company_id>/select/", views.select_company, name="select_company"),
    path("companies/clear/", views.clear_selected_company, name="clear_selected_company"),
    path("workspace/", views.company_workspace, name="company_workspace"),

    # Users
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:user_id>/", views.user_detail, name="user_detail"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:user_id>/password/", views.user_password, name="user_password"),
    path("users/<int:user_id>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),

    # Roles
    path("roles/", views.role_list, name="role_list"),
    path("roles/create/", views.role_create, name="role_create"),
]
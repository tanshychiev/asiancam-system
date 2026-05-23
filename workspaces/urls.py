from django.urls import path

from . import views

urlpatterns = [
    path("", views.workspace_list, name="workspace_list"),
    path("new/", views.workspace_create, name="workspace_create"),
    path("generate-month/", views.workspace_generate_month, name="workspace_generate_month"),

    path("<int:pk>/", views.workspace_detail, name="workspace_detail"),
    path("<int:pk>/edit/", views.workspace_edit, name="workspace_edit"),

    path("<int:pk>/start/", views.workspace_start, name="workspace_start"),
    path("<int:pk>/submit/", views.workspace_submit, name="workspace_submit"),
    path("<int:pk>/approve/", views.workspace_approve, name="workspace_approve"),
    path("<int:pk>/reject/", views.workspace_reject, name="workspace_reject"),
]
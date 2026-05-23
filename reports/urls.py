from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.report_upload, name="report_upload"),
    path("upload/<int:workspace_id>/", views.report_upload, name="report_upload_workspace"),
    path("approvals/", views.report_approval_list, name="report_approval_list"),
    path("<int:pk>/approve/", views.report_approve, name="report_approve"),
    path("<int:pk>/download/", views.report_download, name="report_download"),
]

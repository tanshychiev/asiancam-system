from django.contrib import admin
from .models import ReportFile


@admin.register(ReportFile)
class ReportFileAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "file_type", "visible_to_customer", "is_approved", "uploaded_by", "uploaded_at")
    list_filter = ("file_type", "visible_to_customer", "is_approved")
    search_fields = ("title", "workspace__client__company_name")

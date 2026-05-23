from django.contrib import admin
from .models import MonthlyWorkspace


@admin.register(MonthlyWorkspace)
class MonthlyWorkspaceAdmin(admin.ModelAdmin):
    list_display = ("client", "year", "month", "status", "due_date", "created_at")
    list_filter = ("status", "year", "month")
    search_fields = ("client__company_name", "title")
    filter_horizontal = ("assigned_staff",)

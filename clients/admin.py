from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("company_name", "client_code", "contact_name", "contact_phone", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("company_name", "client_code", "contact_name", "contact_phone", "contact_email")

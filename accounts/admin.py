from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "position", "is_active_staff", "created_at")
    list_filter = ("role", "is_active_staff")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone", "position")

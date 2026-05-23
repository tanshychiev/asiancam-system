from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)

    vatin = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="VATIN / Tax ID",
    )

    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # Staff users who can work on this company
    assigned_staff = models.ManyToManyField(
        User,
        blank=True,
        related_name="assigned_companies",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    USER_TYPE_STAFF = "staff"
    USER_TYPE_CLIENT = "client"

    USER_TYPE_CHOICES = [
        (USER_TYPE_STAFF, "Staff User"),
        (USER_TYPE_CLIENT, "Client User"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=USER_TYPE_STAFF,
    )

    # Only for client user.
    # One company can have many client users.
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="client_users",
        blank=True,
        null=True,
    )

    phone = models.CharField(max_length=50, blank=True)
    position = models.CharField(max_length=100, blank=True)

    can_view_reports = models.BooleanField(default=True)
    can_download_reports = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
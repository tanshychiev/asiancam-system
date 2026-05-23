from django.conf import settings
from django.db import models


class Client(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_PAUSED = "paused"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_PAUSED, "Paused"),
    ]

    company_name = models.CharField(max_length=200)
    client_code = models.CharField(max_length=50, unique=True, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=120, blank=True)

    contact_name = models.CharField(max_length=150, blank=True)
    contact_phone = models.CharField(max_length=80, blank=True)
    contact_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    customer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asiancam_client_accounts",
        help_text="Customer login user for this client.",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asiancam_clients_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name

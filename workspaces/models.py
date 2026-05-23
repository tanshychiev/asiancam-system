from django.conf import settings
from django.db import models
from django.utils import timezone

from clients.models import Client


class MonthlyWorkspace(models.Model):
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_WAITING_CUSTOMER = "waiting_customer"
    STATUS_COMPLETED = "completed"      # Staff completed, waiting admin review
    STATUS_APPROVED = "approved"        # Admin approved, client can view
    STATUS_REJECTED = "rejected"        # Admin returned to staff

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_WAITING_CUSTOMER, "Waiting Customer"),
        (STATUS_COMPLETED, "Completed / Waiting Approval"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected / Return to Staff"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="workspaces")
    year = models.PositiveIntegerField(default=timezone.localdate().year)
    month = models.PositiveIntegerField(default=timezone.localdate().month)

    title = models.CharField(max_length=200, blank=True)

    assigned_staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="asiancam_assigned_workspaces",
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    due_date = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asiancam_workspaces_submitted",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asiancam_workspaces_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asiancam_workspaces_rejected",
    )
    rejected_at = models.DateTimeField(null=True, blank=True)

    review_note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asiancam_workspaces_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "client__company_name"]
        unique_together = ("client", "year", "month")

    def __str__(self):
        return f"{self.client.company_name} - {self.year}-{self.month:02d}"

    @property
    def display_title(self):
        if self.title:
            return self.title
        return f"{self.client.company_name} - {self.year}-{self.month:02d}"

    def start_work(self):
        self.status = self.STATUS_IN_PROGRESS
        self.save(update_fields=["status", "updated_at"])

    def submit_for_review(self, user):
        self.status = self.STATUS_COMPLETED
        self.submitted_by = user
        self.submitted_at = timezone.now()
        self.rejected_by = None
        self.rejected_at = None
        self.save(update_fields=[
            "status",
            "submitted_by",
            "submitted_at",
            "rejected_by",
            "rejected_at",
            "updated_at",
        ])

    def approve(self, user, note=""):
        self.status = self.STATUS_APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.review_note = note or self.review_note
        self.save(update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "review_note",
            "updated_at",
        ])

    def reject(self, user, note=""):
        self.status = self.STATUS_REJECTED
        self.rejected_by = user
        self.rejected_at = timezone.now()
        self.review_note = note
        self.save(update_fields=[
            "status",
            "rejected_by",
            "rejected_at",
            "review_note",
            "updated_at",
        ])
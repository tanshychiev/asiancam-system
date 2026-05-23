from django.conf import settings
from django.db import models
from django.utils import timezone

from workspaces.models import MonthlyWorkspace


def report_upload_path(instance, filename):
    workspace = instance.workspace
    return f"asiancam_reports/{workspace.client_id}/{workspace.year}/{workspace.month:02d}/{filename}"


class ReportFile(models.Model):
    FILE_TYPE_STAFF_IMPORT = "staff_import"
    FILE_TYPE_WORKING_FILE = "working_file"
    FILE_TYPE_FINAL_REPORT = "final_report"

    FILE_TYPE_CHOICES = [
        (FILE_TYPE_STAFF_IMPORT, "Staff Upload / Import"),
        (FILE_TYPE_WORKING_FILE, "Working File"),
        (FILE_TYPE_FINAL_REPORT, "Final Report"),
    ]

    workspace = models.ForeignKey(MonthlyWorkspace, on_delete=models.CASCADE, related_name="report_files")
    title = models.CharField(max_length=200)
    file_type = models.CharField(max_length=30, choices=FILE_TYPE_CHOICES, default=FILE_TYPE_WORKING_FILE)
    file = models.FileField(upload_to=report_upload_path)

    visible_to_customer = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asiancam_reports_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    note = models.TextField(blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asiancam_reports_uploaded",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title

    def approve(self, user):
        self.is_approved = True
        self.visible_to_customer = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["is_approved", "visible_to_customer", "approved_by", "approved_at"])

    def unapprove(self):
        self.is_approved = False
        self.visible_to_customer = False
        self.approved_by = None
        self.approved_at = None
        self.save(update_fields=["is_approved", "visible_to_customer", "approved_by", "approved_at"])

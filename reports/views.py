from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReportFileForm
from .models import ReportFile
from workspaces.models import MonthlyWorkspace


def _is_admin(user):
    if user.is_superuser:
        return True

    profile = getattr(user, "asiancam_profile", None)
    if profile and getattr(profile, "role", None) == "admin":
        return True

    profile = getattr(user, "profile", None)
    if profile and getattr(profile, "user_type", None) == "staff" and user.is_staff:
        return True

    return False


def _is_customer(user):
    profile = getattr(user, "asiancam_profile", None)
    if profile and getattr(profile, "role", None) == "customer":
        return True

    profile = getattr(user, "profile", None)
    if profile and getattr(profile, "user_type", None) == "client":
        return True

    return False


def _can_access_workspace(user, workspace):
    if _is_admin(user):
        return True

    if _is_customer(user):
        return workspace.client.customer_user_id == user.id

    return workspace.assigned_staff.filter(id=user.id).exists()


def _can_upload(user, workspace):
    if _is_admin(user):
        return True

    if _is_customer(user):
        return False

    if workspace.status == MonthlyWorkspace.STATUS_APPROVED:
        return False

    return workspace.assigned_staff.filter(id=user.id).exists()


@login_required
def report_upload(request, workspace_id=None):
    initial = {}
    workspace = None

    if workspace_id:
        workspace = get_object_or_404(MonthlyWorkspace, pk=workspace_id)

        if not _can_upload(request.user, workspace):
            messages.error(request, "You do not have permission to upload to this workspace.")
            return redirect("workspace_detail", pk=workspace.pk)

        initial["workspace"] = workspace

    if request.method == "POST":
        form = ReportFileForm(request.POST, request.FILES)

        if form.is_valid():
            report = form.save(commit=False)

            if not _can_upload(request.user, report.workspace):
                messages.error(request, "You do not have permission to upload to this workspace.")
                return redirect("workspace_list")

            report.uploaded_by = request.user

            if not _is_admin(request.user):
                report.is_approved = False
                report.visible_to_customer = False

            if report.workspace.status == MonthlyWorkspace.STATUS_APPROVED:
                messages.error(request, "Cannot upload to approved workspace.")
                return redirect("workspace_detail", pk=report.workspace.pk)

            report.save()

            if report.workspace.status == MonthlyWorkspace.STATUS_PENDING:
                report.workspace.start_work()

            messages.success(request, "Report/file uploaded.")
            return redirect("workspace_detail", pk=report.workspace.pk)
    else:
        form = ReportFileForm(initial=initial)

    return render(request, "reports/report_upload.html", {
        "form": form,
        "workspace": workspace,
    })


@login_required
def report_approval_list(request):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can approve reports.")
        return redirect("dashboard_home")

    reports = (
        ReportFile.objects
        .filter(is_approved=False)
        .select_related("workspace", "workspace__client", "uploaded_by")
    )

    return render(request, "reports/report_approval_list.html", {
        "reports": reports,
    })


@login_required
def report_approve(request, pk):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can approve reports.")
        return redirect("dashboard_home")

    report = get_object_or_404(ReportFile, pk=pk)

    if request.method == "POST":
        report.approve(request.user)
        messages.success(request, "Report approved and visible to customer.")
        return redirect("workspace_detail", pk=report.workspace.pk)

    return render(request, "reports/report_approve_confirm.html", {
        "report": report,
    })


@login_required
def report_download(request, pk):
    report = get_object_or_404(
        ReportFile.objects.select_related("workspace", "workspace__client"),
        pk=pk,
    )

    if not _can_access_workspace(request.user, report.workspace):
        raise Http404("File not found.")

    if _is_customer(request.user):
        if report.workspace.status != MonthlyWorkspace.STATUS_APPROVED:
            raise Http404("File not found.")

        if not report.is_approved or not report.visible_to_customer:
            raise Http404("File not found.")

    try:
        return FileResponse(
            report.file.open("rb"),
            as_attachment=True,
            filename=report.file.name.split("/")[-1],
        )
    except FileNotFoundError:
        raise Http404("File missing.")
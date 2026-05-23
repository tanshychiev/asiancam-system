from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MonthlyWorkspaceForm
from .models import MonthlyWorkspace
from reports.models import ReportFile


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


def _is_staff_user(user):
    if _is_admin(user):
        return False
    return not _is_customer(user)


def _can_access_workspace(user, workspace):
    if _is_admin(user):
        return True

    if _is_customer(user):
        return workspace.client.customer_user_id == user.id

    return workspace.assigned_staff.filter(id=user.id).exists()


def _can_staff_work(user, workspace):
    if _is_admin(user):
        return False

    if _is_customer(user):
        return False

    return workspace.assigned_staff.filter(id=user.id).exists()


@login_required
def workspace_list(request):
    today = timezone.localdate()
    year = int(request.GET.get("year") or today.year)
    month = int(request.GET.get("month") or today.month)
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()

    workspaces = (
        MonthlyWorkspace.objects
        .select_related("client", "submitted_by", "approved_by", "rejected_by")
        .prefetch_related("assigned_staff")
        .filter(year=year, month=month)
    )

    if not _is_admin(request.user):
        if _is_customer(request.user):
            workspaces = workspaces.filter(client__customer_user=request.user)
        else:
            workspaces = workspaces.filter(assigned_staff=request.user)

    if q:
        workspaces = workspaces.filter(
            Q(client__company_name__icontains=q)
            | Q(title__icontains=q)
            | Q(client__client_code__icontains=q)
        )

    if status:
        workspaces = workspaces.filter(status=status)

    return render(request, "workspaces/workspace_list.html", {
        "workspaces": workspaces.distinct(),
        "year": year,
        "month": month,
        "q": q,
        "status": status,
        "status_choices": MonthlyWorkspace.STATUS_CHOICES,
        "can_create": _is_admin(request.user),
    })


@login_required
def workspace_detail(request, pk):
    workspace = get_object_or_404(
        MonthlyWorkspace.objects
        .select_related("client", "created_by", "submitted_by", "approved_by", "rejected_by")
        .prefetch_related("assigned_staff"),
        pk=pk,
    )

    if not _can_access_workspace(request.user, workspace):
        messages.error(request, "You do not have permission to view this workspace.")
        return redirect("dashboard_home")

    reports = ReportFile.objects.filter(workspace=workspace).select_related("uploaded_by", "approved_by")

    if _is_customer(request.user):
        reports = reports.filter(is_approved=True, visible_to_customer=True)
        if workspace.status != MonthlyWorkspace.STATUS_APPROVED:
            reports = reports.none()

    can_edit = _is_admin(request.user)
    can_upload = _is_admin(request.user) or _can_staff_work(request.user, workspace)

    can_start = (
        _can_staff_work(request.user, workspace)
        and workspace.status in [
            MonthlyWorkspace.STATUS_PENDING,
            MonthlyWorkspace.STATUS_REJECTED,
        ]
    )

    can_submit = (
        _can_staff_work(request.user, workspace)
        and workspace.status in [
            MonthlyWorkspace.STATUS_PENDING,
            MonthlyWorkspace.STATUS_IN_PROGRESS,
            MonthlyWorkspace.STATUS_WAITING_CUSTOMER,
            MonthlyWorkspace.STATUS_REJECTED,
        ]
    )

    can_approve = (
        _is_admin(request.user)
        and workspace.status == MonthlyWorkspace.STATUS_COMPLETED
    )

    can_reject = (
        _is_admin(request.user)
        and workspace.status == MonthlyWorkspace.STATUS_COMPLETED
    )

    return render(request, "workspaces/workspace_detail.html", {
        "workspace": workspace,
        "reports": reports,
        "can_edit": can_edit,
        "can_upload": can_upload,
        "can_start": can_start,
        "can_submit": can_submit,
        "can_approve": can_approve,
        "can_reject": can_reject,
        "is_admin": _is_admin(request.user),
        "is_customer": _is_customer(request.user),
    })


@login_required
def workspace_create(request):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can create workspaces.")
        return redirect("workspace_list")

    if request.method == "POST":
        form = MonthlyWorkspaceForm(request.POST)
        if form.is_valid():
            workspace = form.save(commit=False)
            workspace.created_by = request.user
            workspace.save()
            form.save_m2m()

            messages.success(request, "Monthly workspace created.")
            return redirect("workspace_detail", pk=workspace.pk)
    else:
        form = MonthlyWorkspaceForm()

    return render(request, "workspaces/workspace_form.html", {
        "form": form,
        "title": "Create Monthly Workspace",
    })


@login_required
def workspace_edit(request, pk):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can edit workspaces.")
        return redirect("workspace_detail", pk=pk)

    workspace = get_object_or_404(MonthlyWorkspace, pk=pk)

    if request.method == "POST":
        form = MonthlyWorkspaceForm(request.POST, instance=workspace)
        if form.is_valid():
            form.save()
            messages.success(request, "Monthly workspace updated.")
            return redirect("workspace_detail", pk=workspace.pk)
    else:
        form = MonthlyWorkspaceForm(instance=workspace)

    return render(request, "workspaces/workspace_form.html", {
        "form": form,
        "title": "Edit Monthly Workspace",
        "workspace": workspace,
    })


@login_required
@require_POST
def workspace_start(request, pk):
    workspace = get_object_or_404(MonthlyWorkspace, pk=pk)

    if not _can_staff_work(request.user, workspace):
        messages.error(request, "Only assigned staff can start this workspace.")
        return redirect("workspace_detail", pk=workspace.pk)

    if workspace.status == MonthlyWorkspace.STATUS_APPROVED:
        messages.error(request, "Approved workspace cannot be changed.")
        return redirect("workspace_detail", pk=workspace.pk)

    workspace.start_work()
    messages.success(request, "Workspace marked as In Progress.")
    return redirect("workspace_detail", pk=workspace.pk)


@login_required
@require_POST
def workspace_submit(request, pk):
    workspace = get_object_or_404(MonthlyWorkspace, pk=pk)

    if not _can_staff_work(request.user, workspace):
        messages.error(request, "Only assigned staff can complete this workspace.")
        return redirect("workspace_detail", pk=workspace.pk)

    if workspace.status == MonthlyWorkspace.STATUS_APPROVED:
        messages.error(request, "Approved workspace cannot be submitted again.")
        return redirect("workspace_detail", pk=workspace.pk)

    workspace.submit_for_review(request.user)
    messages.success(request, "Workspace completed and submitted to admin for review.")
    return redirect("workspace_detail", pk=workspace.pk)


@login_required
@require_POST
def workspace_approve(request, pk):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can approve workspace.")
        return redirect("workspace_detail", pk=pk)

    workspace = get_object_or_404(MonthlyWorkspace, pk=pk)
    note = (request.POST.get("review_note") or "").strip()

    workspace.approve(request.user, note=note)

    ReportFile.objects.filter(
        workspace=workspace,
        file_type=ReportFile.FILE_TYPE_FINAL_REPORT,
    ).update(
        is_approved=True,
        visible_to_customer=True,
        approved_by=request.user,
        approved_at=timezone.now(),
    )

    messages.success(request, "Workspace approved. Final reports are now visible to client.")
    return redirect("workspace_detail", pk=workspace.pk)


@login_required
@require_POST
def workspace_reject(request, pk):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can reject workspace.")
        return redirect("workspace_detail", pk=pk)

    workspace = get_object_or_404(MonthlyWorkspace, pk=pk)
    note = (request.POST.get("review_note") or "").strip()

    if not note:
        messages.error(request, "Please enter a reason before returning to staff.")
        return redirect("workspace_detail", pk=workspace.pk)

    workspace.reject(request.user, note=note)

    messages.warning(request, "Workspace returned to staff for correction.")
    return redirect("workspace_detail", pk=workspace.pk)
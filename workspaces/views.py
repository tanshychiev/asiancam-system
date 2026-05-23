from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from clients.models import Client
from reports.models import ReportFile

from .forms import MonthlyWorkspaceForm
from .models import MonthlyWorkspace


# =========================================================
# ROLE HELPERS
# =========================================================

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

    if _is_customer(user):
        return False

    return True


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


# =========================================================
# WORKSPACE LIST
# =========================================================

@login_required
def workspace_list(request):
    today = timezone.localdate()

    try:
        year = int(request.GET.get("year") or today.year)
    except ValueError:
        year = today.year

    try:
        month = int(request.GET.get("month") or today.month)
    except ValueError:
        month = today.month

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()

    workspaces = (
        MonthlyWorkspace.objects
        .select_related(
            "client",
            "submitted_by",
            "approved_by",
            "rejected_by",
        )
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
            | Q(client__client_code__icontains=q)
            | Q(title__icontains=q)
            | Q(assigned_staff__username__icontains=q)
            | Q(assigned_staff__first_name__icontains=q)
            | Q(assigned_staff__last_name__icontains=q)
        )

    if status:
        workspaces = workspaces.filter(status=status)

    workspaces = workspaces.distinct()

    total_count = workspaces.count()
    pending_count = workspaces.filter(status=MonthlyWorkspace.STATUS_PENDING).count()
    progress_count = workspaces.filter(status=MonthlyWorkspace.STATUS_IN_PROGRESS).count()
    waiting_count = workspaces.filter(status=MonthlyWorkspace.STATUS_WAITING_CUSTOMER).count()
    completed_count = workspaces.filter(status=MonthlyWorkspace.STATUS_COMPLETED).count()
    approved_count = workspaces.filter(status=MonthlyWorkspace.STATUS_APPROVED).count()
    rejected_count = workspaces.filter(status=MonthlyWorkspace.STATUS_REJECTED).count()

    month_choices = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    year_choices = list(range(today.year - 3, today.year + 2))

    return render(request, "workspaces/workspace_list.html", {
        "workspaces": workspaces,
        "year": year,
        "month": month,
        "q": q,
        "status": status,
        "status_choices": MonthlyWorkspace.STATUS_CHOICES,
        "month_choices": month_choices,
        "year_choices": year_choices,
        "can_create": _is_admin(request.user),

        "total_count": total_count,
        "pending_count": pending_count,
        "progress_count": progress_count,
        "waiting_count": waiting_count,
        "completed_count": completed_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
    })


# =========================================================
# AUTO GENERATE MONTHLY WORKSPACES
# =========================================================

@login_required
@require_POST
def workspace_generate_month(request):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can generate monthly workspaces.")
        return redirect("workspace_list")

    today = timezone.localdate()

    try:
        year = int(request.POST.get("year") or today.year)
    except ValueError:
        year = today.year

    try:
        month = int(request.POST.get("month") or today.month)
    except ValueError:
        month = today.month

    try:
        due_day = int(request.POST.get("due_day") or 25)
    except ValueError:
        due_day = 25

    if month < 1 or month > 12:
        month = today.month

    if due_day < 1:
        due_day = 1

    if due_day > 28:
        due_day = 28

    due_date = date(year, month, due_day)

    if month == 1:
        previous_year = year - 1
        previous_month = 12
    else:
        previous_year = year
        previous_month = month - 1

    clients = Client.objects.filter(
        status=Client.STATUS_ACTIVE,
    ).order_by("company_name")

    created_count = 0
    skipped_count = 0
    copied_staff_count = 0

    with transaction.atomic():
        for client in clients:
            workspace, created = MonthlyWorkspace.objects.get_or_create(
                client=client,
                year=year,
                month=month,
                defaults={
                    "title": f"{client.company_name} - {year}-{month:02d}",
                    "status": MonthlyWorkspace.STATUS_PENDING,
                    "due_date": due_date,
                    "created_by": request.user,
                },
            )

            if created:
                previous_workspace = (
                    MonthlyWorkspace.objects
                    .filter(
                        client=client,
                        year=previous_year,
                        month=previous_month,
                    )
                    .prefetch_related("assigned_staff")
                    .first()
                )

                if previous_workspace:
                    previous_staff = list(previous_workspace.assigned_staff.all())

                    if previous_staff:
                        workspace.assigned_staff.set(previous_staff)
                        copied_staff_count += 1

                created_count += 1
            else:
                skipped_count += 1

    messages.success(
        request,
        (
            f"Monthly workspaces generated for {month:02d}/{year}. "
            f"Created: {created_count}, skipped existing: {skipped_count}, "
            f"copied staff from last month: {copied_staff_count}."
        ),
    )

    return redirect(f"/workspaces/?year={year}&month={month}")


# =========================================================
# WORKSPACE DETAIL
# =========================================================

@login_required
def workspace_detail(request, pk):
    workspace = get_object_or_404(
        MonthlyWorkspace.objects
        .select_related(
            "client",
            "created_by",
            "submitted_by",
            "approved_by",
            "rejected_by",
        )
        .prefetch_related("assigned_staff"),
        pk=pk,
    )

    if not _can_access_workspace(request.user, workspace):
        messages.error(request, "You do not have permission to view this workspace.")
        return redirect("dashboard_home")

    reports = ReportFile.objects.filter(
        workspace=workspace,
    ).select_related(
        "uploaded_by",
        "approved_by",
    )

    if _is_customer(request.user):
        reports = reports.filter(
            is_approved=True,
            visible_to_customer=True,
        )

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


# =========================================================
# CREATE / EDIT
# =========================================================

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


# =========================================================
# STAFF ACTIONS
# =========================================================

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


# =========================================================
# ADMIN REVIEW ACTIONS
# =========================================================

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
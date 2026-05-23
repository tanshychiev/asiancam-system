from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages

from clients.models import Client
from workspaces.models import MonthlyWorkspace
from reports.models import ReportFile

from core.models import Company


# =========================================================
# ROLE HELPER
# =========================================================

def _role(user):
    """
    AsianCam user types:
    - admin  = superuser
    - staff  = internal accounting staff
    - client = customer/client portal user
    """

    if user.is_superuser:
        return "admin"

    # New profile style: user.profile.user_type = staff/client
    profile = getattr(user, "profile", None)
    if profile and hasattr(profile, "user_type"):
        if profile.user_type == "client":
            return "client"
        return "staff"

    # Old profile style: user.asiancam_profile.role = staff/customer
    old_profile = getattr(user, "asiancam_profile", None)
    if old_profile and hasattr(old_profile, "role"):
        if old_profile.role in ["customer", "client"]:
            return "client"
        return old_profile.role

    return "staff"


def _client_company(user):
    """
    For client user:
    client user belongs under one company.
    """

    profile = getattr(user, "profile", None)

    if profile and hasattr(profile, "company"):
        return profile.company

    return None


# =========================================================
# DASHBOARD HOME
# =========================================================

@login_required
def dashboard_home(request):
    today = timezone.localdate()
    role = _role(request.user)

    clients = Client.objects.all()
    workspaces = MonthlyWorkspace.objects.filter(
        year=today.year,
        month=today.month,
    )
    reports = ReportFile.objects.all()

    selected_company_id = request.session.get("selected_company_id")
    selected_company = None

    if selected_company_id:
        selected_company = Company.objects.filter(
            id=selected_company_id,
            is_active=True,
        ).first()

    # =====================================================
    # CLIENT USER
    # =====================================================
    if role == "client":
        company = _client_company(request.user)

        if company:
            # If your Client model has company field, this works.
            # If not, it will simply skip this filter safely below.
            try:
                clients = clients.filter(company=company)
                workspaces = workspaces.filter(client__company=company)
                reports = reports.filter(workspace__client__company=company)
            except Exception:
                clients = clients.none()
                workspaces = workspaces.none()
                reports = reports.none()
        else:
            # Old system fallback: Client.customer_user
            clients = clients.filter(customer_user=request.user)
            workspaces = workspaces.filter(client__customer_user=request.user)
            reports = reports.filter(workspace__client__customer_user=request.user)

        reports = reports.filter(
            is_approved=True,
            visible_to_customer=True,
        )

    # =====================================================
    # STAFF USER
    # =====================================================
    elif role == "staff":
        # Staff only sees assigned workspaces/clients/reports.
        clients = clients.filter(
            workspaces__assigned_staff=request.user
        ).distinct()

        workspaces = workspaces.filter(
            assigned_staff=request.user
        )

        reports = reports.filter(
            workspace__assigned_staff=request.user
        )

    # =====================================================
    # ADMIN USER
    # =====================================================
    else:
        # Admin sees all.
        pass

    stats = {
        "total_clients": clients.distinct().count(),
        "this_month_workspaces": workspaces.distinct().count(),
        "pending_tasks": workspaces.filter(
            status=MonthlyWorkspace.STATUS_PENDING
        ).distinct().count(),
        "waiting_customer": workspaces.filter(
            status=MonthlyWorkspace.STATUS_WAITING_CUSTOMER
        ).distinct().count(),
        "completed": workspaces.filter(
            status=MonthlyWorkspace.STATUS_COMPLETED
        ).distinct().count(),
        "waiting_approval": (
            ReportFile.objects.filter(is_approved=False).count()
            if role == "admin"
            else 0
        ),
        "approved_reports": reports.filter(
            is_approved=True,
            visible_to_customer=True,
        ).count(),
    }

    latest_workspaces = (
        workspaces
        .select_related("client")
        .distinct()
        .order_by("-id")[:10]
    )

    latest_reports = (
        reports
        .select_related("workspace", "workspace__client")
        .distinct()
        .order_by("-id")[:10]
    )

    return render(request, "dashboard/home.html", {
        "role": role,
        "stats": stats,
        "latest_workspaces": latest_workspaces,
        "latest_reports": latest_reports,
        "today": today,
        "selected_company": selected_company,
    })


# =========================================================
# COMPANY LIST / SELECT COMPANY
# =========================================================

@login_required
def company_list(request):
    query = (request.GET.get("q") or "").strip()
    role = _role(request.user)

    # =====================================================
    # ADMIN
    # Admin can view all active companies.
    # =====================================================
    if request.user.is_superuser or role == "admin":
        companies = Company.objects.filter(is_active=True)

    # =====================================================
    # CLIENT USER
    # Client user sees only their own company.
    # =====================================================
    elif role == "client":
        company = _client_company(request.user)

        if company:
            companies = Company.objects.filter(
                id=company.id,
                is_active=True,
            )
        else:
            companies = Company.objects.none()

    # =====================================================
    # STAFF USER
    # Staff sees only assigned companies.
    # =====================================================
    else:
        companies = Company.objects.filter(
            is_active=True,
            assigned_staff=request.user,
        )

    if query:
        companies = companies.filter(
            Q(name__icontains=query)
            | Q(code__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(vatin__icontains=query)
        )

    companies = (
        companies
        .distinct()
        .prefetch_related("assigned_staff", "client_users")
        .annotate(
            assigned_staff_count=Count("assigned_staff", distinct=True),
            client_user_count=Count("client_users", distinct=True),
        )
        .order_by("name")
    )

    selected_company_id = request.session.get("selected_company_id")
    selected_company = None

    if selected_company_id:
        selected_company = Company.objects.filter(
            id=selected_company_id,
            is_active=True,
        ).first()

    return render(request, "companies/company_list.html", {
        "companies": companies,
        "query": query,
        "total_companies": companies.count(),
        "selected_company": selected_company,
        "role": role,
    })


@login_required
def select_company(request, company_id):
    role = _role(request.user)

    company = get_object_or_404(
        Company,
        id=company_id,
        is_active=True,
    )

    # Staff can only select assigned company.
    if role == "staff" and not request.user.is_superuser:
        has_permission = company.assigned_staff.filter(
            id=request.user.id
        ).exists()

        if not has_permission:
            messages.error(request, "You do not have permission to access this company.")
            return redirect("company_list")

    # Client can only select own company.
    if role == "client":
        client_company = _client_company(request.user)

        if not client_company or client_company.id != company.id:
            messages.error(request, "You can only access your own company.")
            return redirect("company_list")

    request.session["selected_company_id"] = company.id
    request.session["selected_company_name"] = company.name

    messages.success(request, f"Selected company: {company.name}")
    return redirect("dashboard_home")


@login_required
def clear_selected_company(request):
    request.session.pop("selected_company_id", None)
    request.session.pop("selected_company_name", None)

    messages.success(request, "Company selection cleared.")
    return redirect("company_list")
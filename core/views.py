from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AssignStaffForm,
    CompanyCreateForm,
    RoleCreateForm,
    StaffPasswordChangeForm,
    StaffUserCreateForm,
    StaffUserEditForm,
)
from .models import Company, UserProfile


# =========================================================
# HELPERS
# =========================================================

def admin_required(user):
    return user.is_authenticated and user.is_superuser


def get_user_type(user):
    if user.is_superuser:
        return "admin"

    profile = getattr(user, "profile", None)
    if profile:
        return profile.user_type

    return "staff"


def get_client_company(user):
    profile = getattr(user, "profile", None)
    if profile and profile.user_type == "client":
        return profile.company

    return None


# =========================================================
# COMPANY
# =========================================================

@login_required
def company_list(request):
    query = (request.GET.get("q") or "").strip()
    user_type = get_user_type(request.user)

    if request.user.is_superuser:
        companies = Company.objects.filter(is_active=True)

    elif user_type == "client":
        client_company = get_client_company(request.user)

        if client_company:
            companies = Company.objects.filter(
                id=client_company.id,
                is_active=True,
            )
        else:
            companies = Company.objects.none()

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
        "user_type": user_type,
    })


@login_required
@user_passes_test(admin_required)
def company_create(request):
    if request.method == "POST":
        form = CompanyCreateForm(request.POST, request.FILES)

        if form.is_valid():
            company = form.save(commit=False)

            if request.POST.get("remove_logo") == "1":
                company.logo = None

            company.save()
            form.save_m2m()

            messages.success(request, f"Company {company.name} created successfully.")
            return redirect("company_list")
    else:
        form = CompanyCreateForm(initial={"is_active": True})

    return render(request, "companies/company_create.html", {
        "form": form,
    })


@login_required
def select_company(request, company_id):
    company = get_object_or_404(
        Company,
        id=company_id,
        is_active=True,
    )

    user_type = get_user_type(request.user)

    if user_type == "staff" and not request.user.is_superuser:
        has_permission = company.assigned_staff.filter(id=request.user.id).exists()

        if not has_permission:
            messages.error(request, "You do not have permission to access this company.")
            return redirect("company_list")

    if user_type == "client":
        client_company = get_client_company(request.user)

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


@login_required
def company_workspace(request):
    company_id = request.session.get("selected_company_id")

    if not company_id:
        messages.warning(request, "Please select a company first.")
        return redirect("company_list")

    company = get_object_or_404(
        Company,
        id=company_id,
        is_active=True,
    )

    user_type = get_user_type(request.user)

    if user_type == "staff" and not request.user.is_superuser:
        if not company.assigned_staff.filter(id=request.user.id).exists():
            messages.error(request, "You do not have permission to access this company.")
            return redirect("company_list")

    if user_type == "client":
        client_company = get_client_company(request.user)

        if not client_company or client_company.id != company.id:
            messages.error(request, "You can only access your own company.")
            return redirect("company_list")

    return render(request, "companies/company_workspace.html", {
        "company": company,
    })


# =========================================================
# ASSIGN STAFF TO COMPANY
# =========================================================

@login_required
@user_passes_test(admin_required)
def assign_staff(request):
    if request.method == "POST":
        form = AssignStaffForm(request.POST)

        if form.is_valid():
            company = form.cleaned_data["company"]
            staff = form.cleaned_data["staff"]

            company.assigned_staff.set(staff)

            messages.success(request, f"Staff assignment updated for {company.name}.")
            return redirect("company_list")
    else:
        form = AssignStaffForm()

    return render(request, "companies/assign_staff.html", {
        "form": form,
    })


# =========================================================
# USERS
# =========================================================

@login_required
@user_passes_test(admin_required)
def user_list(request):
    query = (request.GET.get("q") or "").strip()
    user_type = (request.GET.get("user_type") or "").strip()
    status = (request.GET.get("status") or "").strip()

    users = (
        User.objects
        .select_related("profile", "profile__company")
        .prefetch_related("groups", "assigned_companies")
        .all()
        .order_by("-date_joined")
    )

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(profile__phone__icontains=query)
            | Q(profile__company__name__icontains=query)
        )

    if user_type == "staff":
        users = users.filter(profile__user_type="staff")
    elif user_type == "client":
        users = users.filter(profile__user_type="client")

    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)

    users = users.distinct()

    total_users = users.count()
    staff_count = users.filter(profile__user_type="staff").count()
    client_count = users.filter(profile__user_type="client").count()
    active_count = users.filter(is_active=True).count()

    return render(request, "users/user_list.html", {
        "users": users,
        "query": query,
        "user_type": user_type,
        "status": status,
        "total_users": total_users,
        "staff_count": staff_count,
        "client_count": client_count,
        "active_count": active_count,
    })


@login_required
@user_passes_test(admin_required)
def user_create(request):
    if request.method == "POST":
        form = StaffUserCreateForm(request.POST)

        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created successfully.")
            return redirect("user_list")
    else:
        form = StaffUserCreateForm(initial={"is_active": True})

    return render(request, "users/user_create.html", {
        "form": form,
    })


@login_required
@user_passes_test(admin_required)
def user_detail(request, user_id):
    user_obj = get_object_or_404(
        User.objects.select_related(
            "profile",
            "profile__company",
        ).prefetch_related(
            "groups",
            "assigned_companies",
        ),
        id=user_id,
    )

    profile, created = UserProfile.objects.get_or_create(
        user=user_obj,
        defaults={"user_type": "staff"},
    )

    assigned_companies = Company.objects.filter(
        assigned_staff=user_obj,
        is_active=True,
    ).order_by("name")

    return render(request, "users/user_detail.html", {
        "user_obj": user_obj,
        "profile": profile,
        "assigned_companies": assigned_companies,
        "assigned_company_count": assigned_companies.count(),
    })


@login_required
@user_passes_test(admin_required)
def user_edit(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    UserProfile.objects.get_or_create(
        user=user_obj,
        defaults={"user_type": "staff"},
    )

    if request.method == "POST":
        form = StaffUserEditForm(request.POST, instance=user_obj)

        if form.is_valid():
            form.save()
            messages.success(request, f"User {user_obj.username} updated successfully.")
            return redirect("user_detail", user_id=user_obj.id)
    else:
        form = StaffUserEditForm(instance=user_obj)

    return render(request, "users/user_edit.html", {
        "form": form,
        "user_obj": user_obj,
    })


@login_required
@user_passes_test(admin_required)
def user_password(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = StaffPasswordChangeForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data["password"]
            user_obj.set_password(password)
            user_obj.save()

            messages.success(request, f"Password updated for {user_obj.username}.")
            return redirect("user_detail", user_id=user_obj.id)
    else:
        form = StaffPasswordChangeForm()

    return render(request, "users/user_password.html", {
        "form": form,
        "user_obj": user_obj,
    })


@login_required
@user_passes_test(admin_required)
def user_toggle_active(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if user_obj.is_superuser and user_obj.id == request.user.id:
        messages.error(request, "You cannot deactivate your own super admin account.")
        return redirect("user_detail", user_id=user_obj.id)

    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=["is_active"])

    if user_obj.is_active:
        messages.success(request, f"User {user_obj.username} is now active.")
    else:
        messages.warning(request, f"User {user_obj.username} is now inactive.")

    return redirect("user_detail", user_id=user_obj.id)


# =========================================================
# ROLES
# =========================================================

@login_required
@user_passes_test(admin_required)
def role_list(request):
    roles = (
        Group.objects
        .prefetch_related("permissions")
        .all()
        .order_by("name")
    )

    return render(request, "roles/role_list.html", {
        "roles": roles,
    })


@login_required
@user_passes_test(admin_required)
def role_create(request):
    if request.method == "POST":
        form = RoleCreateForm(request.POST)

        if form.is_valid():
            role = form.save()
            messages.success(request, f"Role {role.name} created successfully.")
            return redirect("role_list")

        selected_permission_ids = request.POST.getlist("permissions")
    else:
        form = RoleCreateForm()
        selected_permission_ids = []

    permission_modules = defaultdict(lambda: {
        "title": "",
        "view": [],
        "add": [],
        "change": [],
        "delete": [],
        "other": [],
    })

    module_names = {
        "auth": "Users / Roles / Permissions",
        "core": "Companies / Staff Assignment",
        "dashboard": "Dashboard",
        "clients": "Clients",
        "workspaces": "Monthly Workspaces",
        "reports": "Reports",
        "admin": "Admin Logs",
        "sessions": "Sessions",
        "contenttypes": "System Content Types",
    }

    hidden_apps = [
        "admin",
        "sessions",
        "contenttypes",
    ]

    permissions = (
        Permission.objects
        .select_related("content_type")
        .exclude(content_type__app_label__in=hidden_apps)
        .order_by(
            "content_type__app_label",
            "content_type__model",
            "codename",
        )
    )

    for permission in permissions:
        app_label = permission.content_type.app_label
        module_title = module_names.get(
            app_label,
            app_label.replace("_", " ").title(),
        )

        permission_modules[app_label]["title"] = module_title

        code = permission.codename

        if code.startswith("view_"):
            permission_modules[app_label]["view"].append(permission)
        elif code.startswith("add_"):
            permission_modules[app_label]["add"].append(permission)
        elif code.startswith("change_"):
            permission_modules[app_label]["change"].append(permission)
        elif code.startswith("delete_"):
            permission_modules[app_label]["delete"].append(permission)
        else:
            permission_modules[app_label]["other"].append(permission)

    permission_modules = dict(permission_modules)
    total_permissions = permissions.count()

    return render(request, "roles/role_create.html", {
        "form": form,
        "permission_modules": permission_modules,
        "selected_permission_ids": selected_permission_ids,
        "total_permissions": total_permissions,
    })


@login_required
@user_passes_test(admin_required)
def company_edit(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        form = CompanyCreateForm(request.POST, request.FILES, instance=company)

        if form.is_valid():
            old_logo = company.logo
            company = form.save(commit=False)

            if request.POST.get("remove_logo") == "1":
                if old_logo:
                    old_logo.delete(save=False)

                company.logo = None

            company.save()
            form.save_m2m()

            messages.success(request, f"Company {company.name} updated successfully.")
            return redirect("company_list")
    else:
        form = CompanyCreateForm(instance=company)

    return render(request, "companies/company_create.html", {
        "form": form,
        "company": company,
        "is_edit": True,
    })
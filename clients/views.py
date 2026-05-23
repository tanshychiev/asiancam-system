from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client
from workspaces.models import MonthlyWorkspace


def _is_admin(user):
    if user.is_superuser:
        return True
    profile = getattr(user, "asiancam_profile", None)
    return bool(profile and profile.role == "admin")


@login_required
def client_list(request):
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()

    clients = Client.objects.select_related("customer_user").all()

    if not _is_admin(request.user):
        profile = getattr(request.user, "asiancam_profile", None)
        if profile and profile.role == "customer":
            clients = clients.filter(customer_user=request.user)
        else:
            clients = clients.filter(workspaces__assigned_staff=request.user).distinct()

    if q:
        clients = clients.filter(
            Q(company_name__icontains=q)
            | Q(client_code__icontains=q)
            | Q(contact_name__icontains=q)
            | Q(contact_phone__icontains=q)
            | Q(contact_email__icontains=q)
        )

    if status:
        clients = clients.filter(status=status)

    return render(request, "clients/client_list.html", {
        "clients": clients,
        "q": q,
        "status": status,
        "status_choices": Client.STATUS_CHOICES,
        "can_create": _is_admin(request.user),
    })


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if not _is_admin(request.user):
        profile = getattr(request.user, "asiancam_profile", None)
        if profile and profile.role == "customer" and client.customer_user_id != request.user.id:
            messages.error(request, "You do not have permission to view this client.")
            return redirect("dashboard_home")
        if profile and profile.role == "staff":
            allowed = client.workspaces.filter(assigned_staff=request.user).exists()
            if not allowed:
                messages.error(request, "You do not have permission to view this client.")
                return redirect("dashboard_home")

    workspaces = MonthlyWorkspace.objects.filter(client=client).select_related("client").prefetch_related("assigned_staff")
    return render(request, "clients/client_detail.html", {
        "client": client,
        "workspaces": workspaces,
        "can_edit": _is_admin(request.user),
    })


@login_required
def client_create(request):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can create clients.")
        return redirect("client_list")

    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()
            messages.success(request, "Client created.")
            return redirect("client_detail", pk=client.pk)
    else:
        form = ClientForm()

    return render(request, "clients/client_form.html", {"form": form, "title": "Create Client"})


@login_required
def client_edit(request, pk):
    if not _is_admin(request.user):
        messages.error(request, "Only admin can edit clients.")
        return redirect("client_detail", pk=pk)

    client = get_object_or_404(Client, pk=pk)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client updated.")
            return redirect("client_detail", pk=client.pk)
    else:
        form = ClientForm(instance=client)

    return render(request, "clients/client_form.html", {"form": form, "title": "Edit Client"})

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import Company
from accounting.models import JournalEntry, JournalEntryLine

from .forms import VendorForm, VendorTransactionForm
from .models import Vendor, VendorTransaction


# =========================================================
# HELPERS
# =========================================================

def get_selected_company(request):
    company_id = request.session.get("selected_company_id")

    if not company_id:
        return None

    return Company.objects.filter(id=company_id, is_active=True).first()


def can_access_company(user, company):
    if not company:
        return False

    if user.is_superuser:
        return True

    profile = getattr(user, "profile", None)

    if profile and getattr(profile, "user_type", None) == "client":
        return profile.company_id == company.id

    if hasattr(company, "assigned_staff"):
        return company.assigned_staff.filter(id=user.id).exists()

    return False


def require_company_access(request):
    company = get_selected_company(request)

    if not company:
        messages.warning(request, "Please select a company first.")
        return None, redirect("company_list")

    if not can_access_company(request.user, company):
        messages.error(request, "You do not have permission to access this company.")
        return None, redirect("company_list")

    return company, None


def get_posted_status():
    return getattr(JournalEntry, "STATUS_POSTED", "posted")


def create_vendor_journal(transaction_obj, user):
    """
    Auto journal logic:

    Purchase Order / Bill:
        Dr Expense / Inventory
        Cr Account Payable

    Cash Expense:
        Dr Expense
        Cr Cash / Bank

    Vendor Payment:
        Dr Account Payable
        Cr Cash / Bank

    Because we create JournalEntryLine, your existing reports auto include this.
    """

    if transaction_obj.status != VendorTransaction.STATUS_POSTED:
        return None

    with transaction.atomic():
        old_entry = transaction_obj.journal_entry

        if old_entry:
            old_entry.delete()

        entry = JournalEntry.objects.create(
            company=transaction_obj.company,
            entry_date=transaction_obj.transaction_date,
            reference_no=transaction_obj.number or transaction_obj.po_number,
            description=f"{transaction_obj.get_transaction_type_display()} - {transaction_obj.vendor.name if transaction_obj.vendor else 'No Vendor'}",
            status=get_posted_status(),
            created_by=user,
        )

        JournalEntryLine.objects.create(
            entry=entry,
            account=transaction_obj.debit_account,
            description=transaction_obj.memo or transaction_obj.get_transaction_type_display(),
            debit=transaction_obj.amount,
            credit=Decimal("0.00"),
        )

        JournalEntryLine.objects.create(
            entry=entry,
            account=transaction_obj.credit_account,
            description=transaction_obj.memo or transaction_obj.get_transaction_type_display(),
            debit=Decimal("0.00"),
            credit=transaction_obj.amount,
        )

        transaction_obj.journal_entry = entry
        transaction_obj.save(update_fields=["journal_entry"])

        return entry


# =========================================================
# VENDOR CENTER
# =========================================================

@login_required
def vendor_center(request):
    company, response = require_company_access(request)
    if response:
        return response

    query = (request.GET.get("q") or "").strip()

    vendors = Vendor.objects.filter(company=company)

    if query:
        vendors = vendors.filter(
            Q(name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(contact_person__icontains=query)
        )

    vendors = vendors.order_by("name")

    total_vendors = vendors.count()
    active_vendors = vendors.filter(is_active=True).count()

    posted_transactions = VendorTransaction.objects.filter(
        company=company,
        status=VendorTransaction.STATUS_POSTED,
    )

    total_purchase = posted_transactions.filter(
        transaction_type=VendorTransaction.TYPE_PURCHASE_ORDER,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    total_cash_expense = posted_transactions.filter(
        transaction_type=VendorTransaction.TYPE_CASH_EXPENSE,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    total_payment = posted_transactions.filter(
        transaction_type=VendorTransaction.TYPE_VENDOR_PAYMENT,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    ap_balance = total_purchase - total_payment

    return render(request, "vendors/vendor_center.html", {
        "company": company,
        "vendors": vendors,
        "query": query,
        "total_vendors": total_vendors,
        "active_vendors": active_vendors,
        "total_purchase": total_purchase,
        "total_cash_expense": total_cash_expense,
        "total_payment": total_payment,
        "ap_balance": ap_balance,
    })


@login_required
def vendor_create(request):
    company, response = require_company_access(request)
    if response:
        return response

    if request.method == "POST":
        form = VendorForm(request.POST)

        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.company = company
            vendor.created_by = request.user
            vendor.save()

            messages.success(request, f"Vendor {vendor.name} created successfully.")
            return redirect("vendor_center")
    else:
        form = VendorForm(initial={"is_active": True})

    return render(request, "vendors/vendor_form.html", {
        "company": company,
        "form": form,
        "page_title": "Create Vendor",
        "button_text": "Create Vendor",
    })


@login_required
def vendor_edit(request, vendor_id):
    company, response = require_company_access(request)
    if response:
        return response

    vendor = get_object_or_404(Vendor, id=vendor_id, company=company)

    if request.method == "POST":
        form = VendorForm(request.POST, instance=vendor)

        if form.is_valid():
            form.save()
            messages.success(request, f"Vendor {vendor.name} updated successfully.")
            return redirect("vendor_center")
    else:
        form = VendorForm(instance=vendor)

    return render(request, "vendors/vendor_form.html", {
        "company": company,
        "form": form,
        "vendor": vendor,
        "page_title": "Edit Vendor",
        "button_text": "Save Changes",
    })


# =========================================================
# VENDOR TRANSACTIONS
# =========================================================

@login_required
def vendor_transaction_list(request):
    company, response = require_company_access(request)
    if response:
        return response

    query = (request.GET.get("q") or "").strip()
    tran_type = (request.GET.get("type") or "").strip()
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()

    if not date_from and not date_to:
        today = timezone.localdate()
        date_from = today.replace(day=1).strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")

    transactions = VendorTransaction.objects.filter(company=company)

    if query:
        transactions = transactions.filter(
            Q(vendor__name__icontains=query)
            | Q(number__icontains=query)
            | Q(po_number__icontains=query)
            | Q(memo__icontains=query)
        )

    if tran_type:
        transactions = transactions.filter(transaction_type=tran_type)

    if date_from:
        transactions = transactions.filter(transaction_date__gte=date_from)

    if date_to:
        transactions = transactions.filter(transaction_date__lte=date_to)

    transactions = transactions.select_related(
        "vendor",
        "debit_account",
        "credit_account",
        "journal_entry",
    ).order_by("-transaction_date", "-id")

    total_amount = transactions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    return render(request, "vendors/vendor_transaction_list.html", {
        "company": company,
        "transactions": transactions,
        "query": query,
        "tran_type": tran_type,
        "date_from": date_from,
        "date_to": date_to,
        "total_amount": total_amount,
        "type_choices": VendorTransaction.TYPE_CHOICES,
    })


@login_required
def vendor_transaction_create(request, transaction_type=None):
    company, response = require_company_access(request)
    if response:
        return response

    if request.method == "POST":
        form = VendorTransactionForm(
            request.POST,
            company=company,
            transaction_type=transaction_type,
        )

        if form.is_valid():
            with transaction.atomic():
                vendor_transaction = form.save(commit=False)
                vendor_transaction.company = company
                vendor_transaction.created_by = request.user

                if transaction_type:
                    vendor_transaction.transaction_type = transaction_type

                vendor_transaction.save()
                create_vendor_journal(vendor_transaction, request.user)

            messages.success(request, "Vendor transaction saved and journal entry generated.")
            return redirect("vendor_transaction_list")
    else:
        form = VendorTransactionForm(
            company=company,
            transaction_type=transaction_type,
            initial={
                "transaction_date": timezone.localdate(),
                "status": VendorTransaction.STATUS_POSTED,
                "transaction_type": transaction_type or VendorTransaction.TYPE_PURCHASE_ORDER,
            },
        )

    title_map = {
        VendorTransaction.TYPE_PURCHASE_ORDER: "Purchase Order / Bill",
        VendorTransaction.TYPE_CASH_EXPENSE: "Cash Expense",
        VendorTransaction.TYPE_VENDOR_PAYMENT: "Vendor Payment",
    }

    return render(request, "vendors/vendor_transaction_form.html", {
        "company": company,
        "form": form,
        "page_title": title_map.get(transaction_type, "Vendor Transaction"),
        "button_text": "Save & Generate Journal",
    })


@login_required
def vendor_transaction_detail(request, transaction_id):
    company, response = require_company_access(request)
    if response:
        return response

    vendor_transaction = get_object_or_404(
        VendorTransaction.objects.select_related(
            "vendor",
            "debit_account",
            "credit_account",
            "journal_entry",
        ),
        id=transaction_id,
        company=company,
    )

    return render(request, "vendors/vendor_transaction_detail.html", {
        "company": company,
        "transaction": vendor_transaction,
    })
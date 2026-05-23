from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounting.models import JournalEntry, JournalEntryLine
from core.models import Company

from .forms import (
    ItemBrandForm,
    ItemForm,
    ItemGroupForm,
    StockDocumentForm,
    StockDocumentLineFormSet,
    UnitSetForm,
    WarehouseForm,
)
from .models import (
    Item,
    ItemBrand,
    ItemGroup,
    StockDocument,
    UnitSet,
    Warehouse,
)


# =========================================================
# HELPERS
# =========================================================

def get_selected_company(request):
    company_id = request.session.get("selected_company_id")

    if not company_id:
        return None

    return Company.objects.filter(
        id=company_id,
        is_active=True,
    ).first()


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


def create_stock_journal(stock_doc, user):
    """
    Auto journal logic.

    Stock Issue example:
        Dr COGS / Expense
        Cr Inventory Asset

    Stock Adjustment example:
        Dr Inventory / Adjustment Loss
        Cr Inventory / Adjustment Gain

    Stock Transfer:
        No journal because it only moves stock between warehouses.

    Stock Assembly:
        Can create journal if debit/credit accounts are selected.
    """

    if stock_doc.status != StockDocument.STATUS_POSTED:
        return None

    if stock_doc.document_type == StockDocument.TYPE_TRANSFER:
        return None

    if not stock_doc.debit_account or not stock_doc.credit_account:
        return None

    total_amount = stock_doc.total_amount

    if total_amount <= 0:
        return None

    with transaction.atomic():
        old_entry = stock_doc.journal_entry

        if old_entry:
            old_entry.delete()

        entry = JournalEntry.objects.create(
            company=stock_doc.company,
            entry_date=stock_doc.document_date,
            reference_no=stock_doc.number,
            description=f"{stock_doc.get_document_type_display()} - {stock_doc.memo}",
            status=get_posted_status(),
            created_by=user,
        )

        JournalEntryLine.objects.create(
            journal_entry=entry,
            account=stock_doc.debit_account,
            description=stock_doc.memo or stock_doc.get_document_type_display(),
            debit=total_amount,
            credit=Decimal("0.00"),
        )

        JournalEntryLine.objects.create(
            journal_entry=entry,
            account=stock_doc.credit_account,
            description=stock_doc.memo or stock_doc.get_document_type_display(),
            debit=Decimal("0.00"),
            credit=total_amount,
        )

        stock_doc.journal_entry = entry
        stock_doc.save(update_fields=["journal_entry"])

        return entry


# =========================================================
# ITEM MASTER
# =========================================================

@login_required
def item_list(request):
    company, response = require_company_access(request)
    if response:
        return response

    query = (request.GET.get("q") or "").strip()
    item_type = (request.GET.get("item_type") or "").strip()
    group_id = (request.GET.get("group") or "").strip()
    brand_id = (request.GET.get("brand") or "").strip()

    items = (
        Item.objects
        .filter(company=company)
        .select_related("item_group", "item_brand", "unit_set")
    )

    if query:
        items = items.filter(
            Q(code__icontains=query)
            | Q(name__icontains=query)
            | Q(memo__icontains=query)
        )

    if item_type:
        items = items.filter(item_type=item_type)

    if group_id:
        items = items.filter(item_group_id=group_id)

    if brand_id:
        items = items.filter(item_brand_id=brand_id)

    items = items.order_by("code", "name")

    groups = ItemGroup.objects.filter(
        company=company,
        is_active=True,
    ).order_by("name")

    brands = ItemBrand.objects.filter(
        company=company,
        is_active=True,
    ).order_by("name")

    return render(request, "stock/item_list.html", {
        "company": company,
        "items": items,
        "query": query,
        "item_type": item_type,
        "group_id": group_id,
        "brand_id": brand_id,
        "item_type_choices": Item.ITEM_TYPE_CHOICES,
        "groups": groups,
        "brands": brands,
    })


@login_required
def item_create(request):
    company, response = require_company_access(request)
    if response:
        return response

    if request.method == "POST":
        form = ItemForm(request.POST, company=company)

        if form.is_valid():
            item = form.save(commit=False)
            item.company = company
            item.save()

            messages.success(request, "Item created successfully.")
            return redirect("stock_item_list")
    else:
        form = ItemForm(
            company=company,
            initial={
                "is_active": True,
            },
        )

    return render(request, "stock/item_form.html", {
        "company": company,
        "form": form,
        "page_title": "Create Item",
        "button_text": "Create Item",
    })


@login_required
def item_edit(request, item_id):
    company, response = require_company_access(request)
    if response:
        return response

    item = get_object_or_404(
        Item,
        id=item_id,
        company=company,
    )

    if request.method == "POST":
        form = ItemForm(
            request.POST,
            instance=item,
            company=company,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Item updated successfully.")
            return redirect("stock_item_list")
    else:
        form = ItemForm(
            instance=item,
            company=company,
        )

    return render(request, "stock/item_form.html", {
        "company": company,
        "form": form,
        "item": item,
        "page_title": "Edit Item",
        "button_text": "Save Changes",
    })


# =========================================================
# MASTER DATA LISTS
# =========================================================

def master_list_view(request, model, template, title):
    company, response = require_company_access(request)
    if response:
        return response

    query = (request.GET.get("q") or "").strip()
    rows = model.objects.filter(company=company)

    if query:
        if model == ItemBrand:
            rows = rows.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
            )

        elif model == UnitSet:
            rows = rows.filter(
                Q(name__icontains=query)
                | Q(base_unit__icontains=query)
                | Q(default_purchase__icontains=query)
                | Q(default_sale__icontains=query)
                | Q(memo__icontains=query)
            )

        elif model == Warehouse:
            rows = rows.filter(
                Q(name__icontains=query)
                | Q(code__icontains=query)
                | Q(memo__icontains=query)
            )

        else:
            rows = rows.filter(
                Q(name__icontains=query)
                | Q(code__icontains=query)
                | Q(memo__icontains=query)
            )

    rows = rows.order_by("name")

    return render(request, template, {
        "company": company,
        "rows": rows,
        "query": query,
        "title": title,
    })


@login_required
def item_group_list(request):
    return master_list_view(
        request,
        ItemGroup,
        "stock/item_group_list.html",
        "Item Group",
    )


@login_required
def item_brand_list(request):
    return master_list_view(
        request,
        ItemBrand,
        "stock/item_brand_list.html",
        "Item Brand",
    )


@login_required
def unit_set_list(request):
    return master_list_view(
        request,
        UnitSet,
        "stock/unit_set_list.html",
        "Unit Set",
    )


@login_required
def warehouse_list(request):
    return master_list_view(
        request,
        Warehouse,
        "stock/warehouse_list.html",
        "Warehouse",
    )


# =========================================================
# MASTER DATA CREATE
# =========================================================

def master_create_view(request, form_class, template, title, redirect_name):
    company, response = require_company_access(request)
    if response:
        return response

    if request.method == "POST":
        form = form_class(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()

            messages.success(request, f"{title} saved successfully.")
            return redirect(redirect_name)
    else:
        form = form_class(
            initial={
                "is_active": True,
            },
        )

    return render(request, template, {
        "company": company,
        "form": form,
        "page_title": title,
        "button_text": "Save",
    })


@login_required
def item_group_create(request):
    return master_create_view(
        request,
        ItemGroupForm,
        "stock/master_form.html",
        "Create Item Group",
        "stock_item_group_list",
    )


@login_required
def item_brand_create(request):
    return master_create_view(
        request,
        ItemBrandForm,
        "stock/master_form.html",
        "Create Item Brand",
        "stock_item_brand_list",
    )


@login_required
def unit_set_create(request):
    return master_create_view(
        request,
        UnitSetForm,
        "stock/master_form.html",
        "Create Unit Set",
        "stock_unit_set_list",
    )


@login_required
def warehouse_create(request):
    return master_create_view(
        request,
        WarehouseForm,
        "stock/master_form.html",
        "Create Warehouse",
        "stock_warehouse_list",
    )


# =========================================================
# STOCK DOCUMENT LIST
# =========================================================

@login_required
def stock_document_list(request, doc_type):
    company, response = require_company_access(request)
    if response:
        return response

    query = (request.GET.get("q") or "").strip()
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()

    if not date_from and not date_to:
        today = timezone.localdate()
        date_from = today.replace(day=1).strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")

    docs = StockDocument.objects.filter(
        company=company,
        document_type=doc_type,
    )

    if query:
        docs = docs.filter(
            Q(number__icontains=query)
            | Q(memo__icontains=query)
            | Q(lines__item__code__icontains=query)
            | Q(lines__item__name__icontains=query)
        ).distinct()

    if date_from:
        docs = docs.filter(document_date__gte=date_from)

    if date_to:
        docs = docs.filter(document_date__lte=date_to)

    docs = (
        docs
        .select_related(
            "warehouse",
            "from_warehouse",
            "to_warehouse",
            "journal_entry",
        )
        .prefetch_related("lines", "lines__item")
        .order_by("-document_date", "-id")
    )

    title_map = {
        StockDocument.TYPE_ISSUE: "Stock Issue",
        StockDocument.TYPE_ADJUSTMENT: "Stock Adjustment",
        StockDocument.TYPE_ASSEMBLY: "Stock Assembly",
        StockDocument.TYPE_TRANSFER: "Stock Transfer",
    }

    return render(request, "stock/stock_document_list.html", {
        "company": company,
        "docs": docs,
        "doc_type": doc_type,
        "title": title_map.get(doc_type, "Stock Document"),
        "query": query,
        "date_from": date_from,
        "date_to": date_to,
    })


# =========================================================
# STOCK DOCUMENT CREATE
# =========================================================

@login_required
def stock_document_create(request, doc_type):
    company, response = require_company_access(request)
    if response:
        return response

    stock_doc = StockDocument(
        company=company,
        document_type=doc_type,
        created_by=request.user,
    )

    if request.method == "POST":
        form = StockDocumentForm(
            request.POST,
            instance=stock_doc,
            company=company,
            document_type=doc_type,
        )

        formset = StockDocumentLineFormSet(
            request.POST,
            instance=stock_doc,
            form_kwargs={
                "company": company,
            },
        )

        if form.is_valid() and formset.is_valid():
            valid_lines = 0

            for line_form in formset:
                cleaned = getattr(line_form, "cleaned_data", None)

                if not cleaned:
                    continue

                if cleaned.get("DELETE", False):
                    continue

                item = cleaned.get("item")
                qty = cleaned.get("qty") or Decimal("0.00")
                unit_cost = cleaned.get("unit_cost") or Decimal("0.00")

                if item and qty > 0 and unit_cost >= 0:
                    valid_lines += 1

            if valid_lines < 1:
                messages.error(request, "Please input at least one item line.")
            else:
                with transaction.atomic():
                    doc = form.save(commit=False)
                    doc.company = company
                    doc.document_type = doc_type
                    doc.created_by = request.user
                    doc.save()

                    formset.instance = doc
                    formset.save()

                    create_stock_journal(doc, request.user)

                messages.success(request, "Stock document saved successfully.")
                return redirect("stock_document_list", doc_type=doc_type)

    else:
        form = StockDocumentForm(
            instance=stock_doc,
            company=company,
            document_type=doc_type,
            initial={
                "document_date": timezone.localdate(),
                "status": StockDocument.STATUS_POSTED,
            },
        )

        formset = StockDocumentLineFormSet(
            instance=stock_doc,
            form_kwargs={
                "company": company,
            },
        )

    title_map = {
        StockDocument.TYPE_ISSUE: "Create Stock Issue",
        StockDocument.TYPE_ADJUSTMENT: "Create Stock Adjustment",
        StockDocument.TYPE_ASSEMBLY: "Create Stock Assembly",
        StockDocument.TYPE_TRANSFER: "Create Stock Transfer",
    }

    return render(request, "stock/stock_document_form.html", {
        "company": company,
        "form": form,
        "formset": formset,
        "doc_type": doc_type,
        "page_title": title_map.get(doc_type, "Create Stock Document"),
        "button_text": "Save & Generate Journal",
    })


# =========================================================
# SHORTCUT LIST VIEWS
# =========================================================

@login_required
def stock_issue_list(request):
    return stock_document_list(
        request,
        StockDocument.TYPE_ISSUE,
    )


@login_required
def stock_adjustment_list(request):
    return stock_document_list(
        request,
        StockDocument.TYPE_ADJUSTMENT,
    )


@login_required
def stock_assembly_list(request):
    return stock_document_list(
        request,
        StockDocument.TYPE_ASSEMBLY,
    )


@login_required
def stock_transfer_list(request):
    return stock_document_list(
        request,
        StockDocument.TYPE_TRANSFER,
    )


# =========================================================
# SHORTCUT CREATE VIEWS
# =========================================================

@login_required
def stock_issue_create(request):
    return stock_document_create(
        request,
        StockDocument.TYPE_ISSUE,
    )


@login_required
def stock_adjustment_create(request):
    return stock_document_create(
        request,
        StockDocument.TYPE_ADJUSTMENT,
    )


@login_required
def stock_assembly_create(request):
    return stock_document_create(
        request,
        StockDocument.TYPE_ASSEMBLY,
    )


@login_required
def stock_transfer_create(request):
    return stock_document_create(
        request,
        StockDocument.TYPE_TRANSFER,
    )
from decimal import Decimal
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from .models import ChartOfAccount, JournalEntryLine
from .views import require_company_access, get_posted_status


REPORT_MENU = [
    {
        "title": "Profit/Loss by Month",
        "url_name": "report_profit_loss_by_month",
        "export_slug": "profit-loss-by-month",
        "description": "Monthly revenue, cost, expense, and net profit.",
    },
    {
        "title": "General Ledger",
        "url_name": "report_general_ledger",
        "export_slug": "general-ledger",
        "description": "Account-by-account journal movement.",
    },
    {
        "title": "AP Aging Summary Detail",
        "url_name": "report_ap_aging",
        "export_slug": "ap-aging",
        "description": "Vendor unpaid purchase / adjustment aging.",
    },
    {
        "title": "AR Aging Summary Detail",
        "url_name": "report_ar_aging",
        "export_slug": "ar-aging",
        "description": "Customer invoice / adjustment aging.",
    },
    {
        "title": "Balance Sheet",
        "url_name": "report_balance_sheet",
        "export_slug": "balance-sheet",
        "description": "Assets, liabilities, equity, and balance check.",
    },
    {
        "title": "Profit/Loss Standard",
        "url_name": "report_profit_loss_standard",
        "export_slug": "profit-loss-standard",
        "description": "Standard profit and loss by account.",
    },
    {
        "title": "Journal Report",
        "url_name": "report_journal_report",
        "export_slug": "journal-report",
        "description": "Posted journal entries and lines.",
    },
    {
        "title": "Trial Balance",
        "url_name": "report_trial_balance",
        "export_slug": "trial-balance",
        "description": "Debit and credit totals by account.",
    },
    {
        "title": "Cash Flow",
        "url_name": "report_cash_flow",
        "export_slug": "cash-flow",
        "description": "Cash account movement based on posted journals.",
    },
]


def _report_dates(request):
    today = timezone.localdate()
    date_from = (request.GET.get("date_from") or today.replace(day=1).strftime("%Y-%m-%d")).strip()
    date_to = (request.GET.get("date_to") or today.strftime("%Y-%m-%d")).strip()

    year = today.year
    try:
        year = datetime.strptime(date_from, "%Y-%m-%d").year
    except Exception:
        pass

    return today, date_from, date_to, year


def _posted_lines(company, date_from=None, date_to=None):
    lines = JournalEntryLine.objects.filter(
        journal_entry__company=company,
        journal_entry__status=get_posted_status(),
    ).select_related("journal_entry", "account")

    if date_from:
        lines = lines.filter(journal_entry__entry_date__gte=date_from)

    if date_to:
        lines = lines.filter(journal_entry__entry_date__lte=date_to)

    return lines


def _signed_balance(account_type, debit, credit):
    if account_type in ["asset", "expense", "cogs", "other_expense"]:
        return debit - credit
    return credit - debit


def _build_account_report_rows(company, date_from, date_to):
    lines = _posted_lines(company, date_from, date_to)

    account_rows = (
        lines
        .values(
            "account_id",
            "account__code",
            "account__name",
            "account__account_type",
            "account__report_type",
            "account__report_section",
            "account__normal_balance",
        )
        .annotate(debit=Sum("debit"), credit=Sum("credit"))
        .order_by("account__code")
    )

    trial_balance_rows = []
    profit_loss_rows = []
    balance_sheet_rows = []

    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")

    total_revenue = Decimal("0.00")
    total_cogs = Decimal("0.00")
    total_expense = Decimal("0.00")
    total_other_income = Decimal("0.00")
    total_other_expense = Decimal("0.00")

    total_assets = Decimal("0.00")
    total_liabilities = Decimal("0.00")
    total_equity = Decimal("0.00")

    for row in account_rows:
        debit = row["debit"] or Decimal("0.00")
        credit = row["credit"] or Decimal("0.00")
        account_type = row["account__account_type"]
        report_type = row["account__report_type"]
        balance = _signed_balance(account_type, debit, credit)

        total_debit += debit
        total_credit += credit

        data = {
            "account_id": row["account_id"],
            "code": row["account__code"],
            "name": row["account__name"],
            "account_type": account_type,
            "report_type": report_type,
            "report_section": row["account__report_section"],
            "normal_balance": row["account__normal_balance"],
            "debit": debit,
            "credit": credit,
            "balance": balance,
        }

        trial_balance_rows.append(data)

        if report_type == ChartOfAccount.REPORT_PROFIT_LOSS:
            profit_loss_rows.append(data)

            if account_type == ChartOfAccount.ACCOUNT_TYPE_REVENUE:
                total_revenue += balance
            elif account_type == ChartOfAccount.ACCOUNT_TYPE_COGS:
                total_cogs += balance
            elif account_type == ChartOfAccount.ACCOUNT_TYPE_EXPENSE:
                total_expense += balance
            elif account_type == ChartOfAccount.ACCOUNT_TYPE_OTHER_INCOME:
                total_other_income += balance
            elif account_type == ChartOfAccount.ACCOUNT_TYPE_OTHER_EXPENSE:
                total_other_expense += balance

        if report_type == ChartOfAccount.REPORT_BALANCE_SHEET:
            balance_sheet_rows.append(data)

            if account_type == ChartOfAccount.ACCOUNT_TYPE_ASSET:
                total_assets += balance
            elif account_type == ChartOfAccount.ACCOUNT_TYPE_LIABILITY:
                total_liabilities += balance
            elif account_type == ChartOfAccount.ACCOUNT_TYPE_EQUITY:
                total_equity += balance

    gross_profit = total_revenue - total_cogs
    net_profit = gross_profit - total_expense + total_other_income - total_other_expense
    balance_check = total_assets - (total_liabilities + total_equity + net_profit)

    return {
        "trial_balance_rows": trial_balance_rows,
        "profit_loss_rows": profit_loss_rows,
        "balance_sheet_rows": balance_sheet_rows,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "total_revenue": total_revenue,
        "total_cogs": total_cogs,
        "gross_profit": gross_profit,
        "total_expense": total_expense,
        "total_other_income": total_other_income,
        "total_other_expense": total_other_expense,
        "net_profit": net_profit,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "balance_check": balance_check,
    }


def _build_profit_loss_by_month(company, year):
    rows = []
    accounts = ChartOfAccount.objects.filter(
        company=company,
        is_active=True,
        is_group=False,
        report_type=ChartOfAccount.REPORT_PROFIT_LOSS,
    ).order_by("code")

    for account in accounts:
        monthly_amounts = []
        row_total = Decimal("0.00")

        for month in range(1, 13):
            sums = JournalEntryLine.objects.filter(
                journal_entry__company=company,
                journal_entry__status=get_posted_status(),
                journal_entry__entry_date__year=year,
                journal_entry__entry_date__month=month,
                account=account,
            ).aggregate(debit=Sum("debit"), credit=Sum("credit"))

            debit = sums["debit"] or Decimal("0.00")
            credit = sums["credit"] or Decimal("0.00")

            if account.account_type in [
                ChartOfAccount.ACCOUNT_TYPE_REVENUE,
                ChartOfAccount.ACCOUNT_TYPE_OTHER_INCOME,
            ]:
                amount = credit - debit
            else:
                amount = debit - credit

            monthly_amounts.append(amount)
            row_total += amount

        if row_total != 0:
            rows.append({
                "account_id": account.id,
                "code": account.code,
                "name": account.name,
                "months": monthly_amounts,
                "total": row_total,
            })

    return rows


def _build_ap_aging(company, today, date_to):
    rows = []

    try:
        from vendors.models import VendorTransaction
    except Exception:
        return rows

    qs = VendorTransaction.objects.filter(
        company=company,
        status=VendorTransaction.STATUS_POSTED,
        transaction_type__in=[
            VendorTransaction.TYPE_PURCHASE_ORDER,
            VendorTransaction.TYPE_ADJUSTMENT,
        ],
    ).select_related("vendor").order_by("vendor__name", "transaction_date")

    if date_to:
        qs = qs.filter(transaction_date__lte=date_to)

    for tx in qs[:300]:
        age = (today - tx.transaction_date).days
        amount = tx.amount or Decimal("0.00")

        rows.append({
            "id": tx.id,
            "vendor": tx.vendor.name if tx.vendor else "-",
            "date": tx.transaction_date,
            "number": tx.number,
            "type": tx.get_transaction_type_display(),
            "current": amount if age <= 0 else Decimal("0.00"),
            "days_1_30": amount if 1 <= age <= 30 else Decimal("0.00"),
            "days_31_60": amount if 31 <= age <= 60 else Decimal("0.00"),
            "days_61_90": amount if 61 <= age <= 90 else Decimal("0.00"),
            "over_90": amount if age > 90 else Decimal("0.00"),
        })

    return rows


def _build_ar_aging(company, today, date_to):
    rows = []

    try:
        from customers.models import CustomerTransaction
    except Exception:
        return rows

    qs = CustomerTransaction.objects.filter(
        company=company,
        status=CustomerTransaction.STATUS_POSTED,
        transaction_type__in=[
            CustomerTransaction.TYPE_INVOICE,
            CustomerTransaction.TYPE_ADJUSTMENT,
        ],
    ).select_related("customer").order_by("customer__name", "transaction_date")

    if date_to:
        qs = qs.filter(transaction_date__lte=date_to)

    for tx in qs[:300]:
        age = (today - tx.transaction_date).days
        amount = tx.amount or Decimal("0.00")

        rows.append({
            "id": tx.id,
            "customer": tx.customer.name,
            "date": tx.transaction_date,
            "number": tx.number,
            "type": tx.get_transaction_type_display(),
            "current": amount if age <= 0 else Decimal("0.00"),
            "days_1_30": amount if 1 <= age <= 30 else Decimal("0.00"),
            "days_31_60": amount if 31 <= age <= 60 else Decimal("0.00"),
            "days_61_90": amount if 61 <= age <= 90 else Decimal("0.00"),
            "over_90": amount if age > 90 else Decimal("0.00"),
        })

    return rows


def _build_cash_flow(company, lines):
    rows = []
    total_cash_change = Decimal("0.00")

    accounts = ChartOfAccount.objects.filter(
        company=company,
        is_active=True,
        is_group=False,
        account_type=ChartOfAccount.ACCOUNT_TYPE_ASSET,
        name__icontains="cash",
    ).order_by("code")

    for account in accounts:
        sums = lines.filter(account=account).aggregate(debit=Sum("debit"), credit=Sum("credit"))

        debit = sums["debit"] or Decimal("0.00")
        credit = sums["credit"] or Decimal("0.00")
        amount = debit - credit

        if amount != 0:
            total_cash_change += amount
            rows.append({
                "account_id": account.id,
                "code": account.code,
                "name": account.name,
                "section": account.report_section,
                "amount": amount,
            })

    return rows, total_cash_change


def _base_context(request, active_report=None):
    company, response = require_company_access(request)
    if response:
        return None, response

    today, date_from, date_to, year = _report_dates(request)
    lines = _posted_lines(company, date_from, date_to)

    account_context = _build_account_report_rows(company, date_from, date_to)
    cash_flow_rows, total_cash_change = _build_cash_flow(company, lines)

    context = {
        "company": company,
        "date_from": date_from,
        "date_to": date_to,
        "report_year": year,
        "reports": REPORT_MENU,
        "active_report": active_report,

        "journal_report_rows": lines.order_by("journal_entry__entry_date", "journal_entry_id", "id")[:300],
        "general_ledger_rows": lines.order_by("journal_entry__entry_date", "journal_entry_id", "id")[:300],
        "pl_month_rows": _build_profit_loss_by_month(company, year),
        "ap_aging_rows": _build_ap_aging(company, today, date_to),
        "ar_aging_rows": _build_ar_aging(company, today, date_to),
        "cash_flow_rows": cash_flow_rows,
        "total_cash_change": total_cash_change,
    }

    context.update(account_context)
    return context, None


@login_required
def report_home(request):
    context, response = _base_context(request, active_report=None)
    if response:
        return response

    return render(request, "accounting/reports/report_home.html", context)


@login_required
def report_profit_loss_by_month(request):
    context, response = _base_context(request, active_report="profit-loss-by-month")
    if response:
        return response

    context.update({
        "report_title": "Profit/Loss by Month",
        "export_slug": "profit-loss-by-month",
    })
    return render(request, "accounting/reports/profit_loss_by_month.html", context)


@login_required
def report_general_ledger(request):
    context, response = _base_context(request, active_report="general-ledger")
    if response:
        return response

    context.update({
        "report_title": "General Ledger",
        "export_slug": "general-ledger",
    })
    return render(request, "accounting/reports/general_ledger.html", context)


@login_required
def report_ap_aging(request):
    context, response = _base_context(request, active_report="ap-aging")
    if response:
        return response

    context.update({
        "report_title": "AP Aging Summary Detail",
        "export_slug": "ap-aging",
    })
    return render(request, "accounting/reports/ap_aging.html", context)


@login_required
def report_ar_aging(request):
    context, response = _base_context(request, active_report="ar-aging")
    if response:
        return response

    context.update({
        "report_title": "AR Aging Summary Detail",
        "export_slug": "ar-aging",
    })
    return render(request, "accounting/reports/ar_aging.html", context)


@login_required
def report_balance_sheet(request):
    context, response = _base_context(request, active_report="balance-sheet")
    if response:
        return response

    context.update({
        "report_title": "Balance Sheet",
        "export_slug": "balance-sheet",
    })
    return render(request, "accounting/reports/balance_sheet.html", context)


@login_required
def report_profit_loss_standard(request):
    context, response = _base_context(request, active_report="profit-loss-standard")
    if response:
        return response

    context.update({
        "report_title": "Profit/Loss Standard",
        "export_slug": "profit-loss-standard",
    })
    return render(request, "accounting/reports/profit_loss_standard.html", context)


@login_required
def report_journal_report(request):
    context, response = _base_context(request, active_report="journal-report")
    if response:
        return response

    context.update({
        "report_title": "Journal Report",
        "export_slug": "journal-report",
    })
    return render(request, "accounting/reports/journal_report.html", context)


@login_required
def report_trial_balance(request):
    context, response = _base_context(request, active_report="trial-balance")
    if response:
        return response

    context.update({
        "report_title": "Trial Balance",
        "export_slug": "trial-balance",
    })
    return render(request, "accounting/reports/trial_balance.html", context)


@login_required
def report_cash_flow(request):
    context, response = _base_context(request, active_report="cash-flow")
    if response:
        return response

    context.update({
        "report_title": "Cash Flow",
        "export_slug": "cash-flow",
    })
    return render(request, "accounting/reports/cash_flow.html", context)

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from core.models import Company
from django.conf import settings


class ChartOfAccount(models.Model):
    ACCOUNT_TYPE_ASSET = "asset"
    ACCOUNT_TYPE_LIABILITY = "liability"
    ACCOUNT_TYPE_EQUITY = "equity"
    ACCOUNT_TYPE_REVENUE = "revenue"
    ACCOUNT_TYPE_COGS = "cogs"
    ACCOUNT_TYPE_EXPENSE = "expense"
    ACCOUNT_TYPE_OTHER_INCOME = "other_income"
    ACCOUNT_TYPE_OTHER_EXPENSE = "other_expense"

    ACCOUNT_TYPE_CHOICES = [
        (ACCOUNT_TYPE_ASSET, "Asset"),
        (ACCOUNT_TYPE_LIABILITY, "Liability"),
        (ACCOUNT_TYPE_EQUITY, "Equity"),
        (ACCOUNT_TYPE_REVENUE, "Revenue"),
        (ACCOUNT_TYPE_COGS, "Cost of Goods Sold"),
        (ACCOUNT_TYPE_EXPENSE, "Expense"),
        (ACCOUNT_TYPE_OTHER_INCOME, "Other Income"),
        (ACCOUNT_TYPE_OTHER_EXPENSE, "Other Expense"),
    ]

    REPORT_BALANCE_SHEET = "balance_sheet"
    REPORT_PROFIT_LOSS = "profit_loss"
    REPORT_CASH_FLOW = "cash_flow"
    REPORT_TRIAL_BALANCE = "trial_balance"

    REPORT_TYPE_CHOICES = [
        (REPORT_BALANCE_SHEET, "Balance Sheet"),
        (REPORT_PROFIT_LOSS, "Profit & Loss"),
        (REPORT_CASH_FLOW, "Cash Flow"),
        (REPORT_TRIAL_BALANCE, "Trial Balance"),
    ]

    NORMAL_DEBIT = "debit"
    NORMAL_CREDIT = "credit"

    NORMAL_BALANCE_CHOICES = [
        (NORMAL_DEBIT, "Debit"),
        (NORMAL_CREDIT, "Credit"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="chart_accounts",
    )

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    local_name = models.CharField(max_length=200, blank=True)

    account_type = models.CharField(
        max_length=30,
        choices=ACCOUNT_TYPE_CHOICES,
    )

    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPE_CHOICES,
    )

    report_section = models.CharField(
        max_length=100,
        blank=True,
        help_text="Example: Current Asset, Current Liability, Revenue, Expense",
    )

    normal_balance = models.CharField(
        max_length=10,
        choices=NORMAL_BALANCE_CHOICES,
        default=NORMAL_DEBIT,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="children",
    )

    is_group = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code", "name"]
        unique_together = ["company", "code"]
        verbose_name = "Chart of Account"
        verbose_name_plural = "Chart of Accounts"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def report_name(self):
        return self.get_report_type_display()

    @property
    def type_name(self):
        return self.get_account_type_display()


class JournalEntry(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_POSTED = "posted"
    STATUS_VOID = "void"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_POSTED, "Posted"),
        (STATUS_VOID, "Void"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="journal_entries",
    )

    entry_date = models.DateField()
    reference_no = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_POSTED,
    )

    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_journal_entries",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-entry_date", "-id"]
        verbose_name = "Journal Entry"
        verbose_name_plural = "Journal Entries"

    def __str__(self):
        return f"{self.entry_no} - {self.company.name}"

    @property
    def entry_no(self):
        if self.id:
            return f"JE-{self.id:05d}"
        return "JE-New"

    @property
    def total_debit(self):
        return self.lines.aggregate(total=models.Sum("debit"))["total"] or Decimal("0.00")

    @property
    def total_credit(self):
        return self.lines.aggregate(total=models.Sum("credit"))["total"] or Decimal("0.00")

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit


class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )

    description = models.CharField(max_length=255, blank=True)

    debit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    credit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Journal Entry Line"
        verbose_name_plural = "Journal Entry Lines"

    def clean(self):
        debit = self.debit or Decimal("0.00")
        credit = self.credit or Decimal("0.00")

        if debit > 0 and credit > 0:
            raise ValidationError("One line cannot have both debit and credit.")

        if debit <= 0 and credit <= 0:
            raise ValidationError("Each line must have debit or credit amount.")

        if self.account and self.journal_entry:
            if self.account.company_id != self.journal_entry.company_id:
                raise ValidationError("Account must belong to the selected company.")

    def __str__(self):
        return f"{self.account.code} - Debit: {self.debit} Credit: {self.credit}"
    

class AccountingEntry(models.Model):
    SOURCE_MANUAL = "manual"
    SOURCE_EXCEL = "excel"

    SOURCE_CHOICES = [
        (SOURCE_MANUAL, "Manual Input"),
        (SOURCE_EXCEL, "Excel Import"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="accounting_entries",
    )
    entry_date = models.DateField()
    reference_no = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_MANUAL,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entry_date", "-id"]

    def __str__(self):
        return f"{self.company} - {self.entry_date} - {self.reference_no}"

    @property
    def total_debit(self):
        return self.lines.aggregate(total=models.Sum("debit"))["total"] or Decimal("0.00")

    @property
    def total_credit(self):
        return self.lines.aggregate(total=models.Sum("credit"))["total"] or Decimal("0.00")

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit


class AccountingEntryLine(models.Model):
    entry = models.ForeignKey(
        AccountingEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    account = models.ForeignKey(
        "ChartOfAccount",
        on_delete=models.PROTECT,
        related_name="entry_lines",
    )

    line_description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.account} Dr {self.debit} Cr {self.credit}"    
    

# =========================================================
# BULK UPDATE MASTER DATA
# Items + Customers imported by Excel
# =========================================================

class AccountItem(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="account_items",
    )

    item = models.CharField(max_length=100)
    item_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=100)

    local_name = models.CharField(max_length=255, blank=True)
    item_group = models.CharField(max_length=255, blank=True)
    item_brand = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    negative_sale = models.BooleanField(default=True)
    for_purchase = models.BooleanField(default=True)
    for_sale = models.BooleanField(default=True)

    alarm_qty = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    account_asset_code = models.CharField(max_length=50, blank=True)
    account_cogs_code = models.CharField(max_length=50, blank=True)
    account_revenue_code = models.CharField(max_length=50, blank=True)

    memo = models.TextField(blank=True)
    detail_memo = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    unitset_name = models.CharField(max_length=100, blank=True)

    price_1 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    barcode_1 = models.CharField(max_length=100, blank=True)

    price_2 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    barcode_2 = models.CharField(max_length=100, blank=True)

    price_3 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    barcode_3 = models.CharField(max_length=100, blank=True)

    imported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item_code", "item_name"]
        unique_together = ["company", "item_code"]
        verbose_name = "Account Item"
        verbose_name_plural = "Account Items"

    def __str__(self):
        return f"{self.item_code} - {self.item_name}"


class AccountCustomer(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="account_customers",
    )

    customer = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=255)
    customer_code = models.CharField(max_length=100)
    local_customer_name = models.CharField(max_length=255, blank=True)

    customer_type = models.CharField(max_length=100, blank=True)
    sale_person = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=50, blank=True)
    price_level = models.CharField(max_length=100, blank=True)
    invoice_type = models.CharField(max_length=100, blank=True)

    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit_term = models.IntegerField(default=0)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=100, blank=True)
    vattin = models.CharField(max_length=100, blank=True)

    is_allow_over_credit = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    house_no = models.CharField(max_length=100, blank=True)
    street = models.CharField(max_length=100, blank=True)
    commune = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    local_house_no = models.CharField(max_length=100, blank=True)
    local_street = models.CharField(max_length=100, blank=True)
    local_commune = models.CharField(max_length=100, blank=True)
    local_district = models.CharField(max_length=100, blank=True)
    local_city = models.CharField(max_length=100, blank=True)

    address = models.TextField(blank=True)
    memo = models.TextField(blank=True)

    contact_name = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)

    branches = models.CharField(max_length=255, blank=True)
    grade = models.CharField(max_length=100, blank=True)

    imported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["customer_code", "customer_name"]
        unique_together = ["company", "customer_code"]
        verbose_name = "Account Customer"
        verbose_name_plural = "Account Customers"

    def __str__(self):
        return f"{self.customer_code} - {self.customer_name}"


class BulkImportLog(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="bulk_import_logs",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounting_bulk_import_logs",
    )

    file_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)

    item_created = models.IntegerField(default=0)
    item_updated = models.IntegerField(default=0)

    customer_created = models.IntegerField(default=0)
    customer_updated = models.IntegerField(default=0)

    error_count = models.IntegerField(default=0)
    error_report = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bulk Import Log"
        verbose_name_plural = "Bulk Import Logs"

    def __str__(self):
        return f"{self.company} - {self.status} - {self.file_name}"    
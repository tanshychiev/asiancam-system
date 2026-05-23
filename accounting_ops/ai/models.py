from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounting.models import ChartOfAccount, JournalEntry
from core.models import Company


class BankAccount(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="bank_accounts",
    )

    name = models.CharField(max_length=150)
    bank_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=20, default="USD")

    chart_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="bank_accounts",
        help_text="Cash/Bank account in Chart of Accounts",
    )

    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class BankDeposit(models.Model):
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
        related_name="bank_deposits",
    )
    deposit_date = models.DateField(default=timezone.localdate)
    number = models.CharField(max_length=80, blank=True)

    deposit_to = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="deposits",
    )

    source_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="bank_deposit_source_lines",
        help_text="Usually Undeposited Funds, Cash on Hand, A/R, or clearing account",
    )

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    memo = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED)

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bank_deposit",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-deposit_date", "-id"]

    def __str__(self):
        return f"{self.number or self.id} - {self.amount}"


class BankRule(models.Model):
    MONEY_IN = "in"
    MONEY_OUT = "out"

    MONEY_DIRECTION_CHOICES = [
        (MONEY_IN, "Money In"),
        (MONEY_OUT, "Money Out"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="bank_rules",
    )

    name = models.CharField(max_length=150)
    priority_order = models.PositiveIntegerField(default=1)
    money_direction = models.CharField(
        max_length=10,
        choices=MONEY_DIRECTION_CHOICES,
        default=MONEY_IN,
    )

    keyword = models.CharField(max_length=180, blank=True)
    target_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="bank_rules",
        null=True,
        blank=True,
    )

    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["priority_order", "name"]

    def __str__(self):
        return self.name


class BankReconcile(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="bank_reconciles",
    )

    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="reconciles",
    )
    reconcile_date = models.DateField(default=timezone.localdate)
    tran_date = models.DateField(null=True, blank=True)

    bank_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    book_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    difference = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    memo = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reconcile_date", "-id"]

    def save(self, *args, **kwargs):
        self.difference = (self.bank_balance or Decimal("0.00")) - (self.book_balance or Decimal("0.00"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bank_account} - {self.reconcile_date}"


class LandedCostAllocation(models.Model):
    METHOD_AMOUNT = "amount"
    METHOD_QTY = "qty"
    METHOD_WEIGHT = "weight"

    METHOD_CHOICES = [
        (METHOD_AMOUNT, "By Amount"),
        (METHOD_QTY, "By Quantity"),
        (METHOD_WEIGHT, "By Weight"),
    ]

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
        related_name="landed_cost_allocations",
    )

    allocation_date = models.DateField(default=timezone.localdate)
    number = models.CharField(max_length=80, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    bill_no = models.CharField(max_length=80, blank=True)
    vendor_name = models.CharField(max_length=180, blank=True)
    po_number = models.CharField(max_length=80, blank=True)

    allocation_method = models.CharField(
        max_length=30,
        choices=METHOD_CHOICES,
        default=METHOD_AMOUNT,
    )

    landed_cost_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="landed_cost_debits",
        help_text="Usually Inventory Asset",
    )
    clearing_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="landed_cost_credits",
        help_text="Usually Freight/Clearing/AP",
    )

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    memo = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED)

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="landed_cost_allocation",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-allocation_date", "-id"]

    def __str__(self):
        return f"{self.number or self.id} - {self.amount}"


class ImportHistory(models.Model):
    TYPE_STOCK_BALANCE = "stock_balance"
    TYPE_ITEM = "item"
    TYPE_VENDOR = "vendor"
    TYPE_CUSTOMER = "customer"
    TYPE_COA = "chart_of_account"
    TYPE_BATCH_TRANSACTION = "batch_transaction"

    # Opening Balance / Client Setup imports
    TYPE_TRIAL_BALANCE = "trial_balance"
    TYPE_JOURNAL_OPENING = "journal_opening"
    TYPE_OUTSTANDING_AP = "outstanding_ap"
    TYPE_OUTSTANDING_AR = "outstanding_ar"

    TYPE_CHOICES = [
        (TYPE_STOCK_BALANCE, "Import Stock Balance"),
        (TYPE_ITEM, "Import Item"),
        (TYPE_VENDOR, "Import Vendor"),
        (TYPE_CUSTOMER, "Import Customer"),
        (TYPE_COA, "Import Chart of Account"),
        (TYPE_BATCH_TRANSACTION, "Batch Transaction"),

        (TYPE_TRIAL_BALANCE, "Trial Balance Full"),
        (TYPE_JOURNAL_OPENING, "Journal Opening Balance"),
        (TYPE_OUTSTANDING_AP, "Outstanding AP"),
        (TYPE_OUTSTANDING_AR, "Outstanding AR"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="import_histories",
    )

    import_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    file = models.FileField(upload_to="accounting_imports/", null=True, blank=True)

    total_rows = models.PositiveIntegerField(default=0)
    success_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)

    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_import_type_display()} - {self.created_at}"
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Company
from accounting.models import ChartOfAccount, JournalEntry


class Vendor(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="vendors",
    )

    name = models.CharField(max_length=180)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    memo = models.TextField(blank=True)

    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name

    @property
    def ap_balance(self):
        transactions = self.transactions.filter(status=VendorTransaction.STATUS_POSTED)
        debit = transactions.aggregate(total=models.Sum("debit_amount"))["total"] or Decimal("0.00")
        credit = transactions.aggregate(total=models.Sum("credit_amount"))["total"] or Decimal("0.00")
        return self.opening_balance + credit - debit


class VendorTransaction(models.Model):
    TYPE_PURCHASE_ORDER = "purchase_order"
    TYPE_CASH_EXPENSE = "cash_expense"
    TYPE_VENDOR_PAYMENT = "vendor_payment"
    TYPE_ADJUSTMENT = "adjustment"

    TYPE_CHOICES = [
        (TYPE_PURCHASE_ORDER, "Purchase Order / Bill"),
        (TYPE_CASH_EXPENSE, "Cash Expense"),
        (TYPE_VENDOR_PAYMENT, "Vendor Payment"),
        (TYPE_ADJUSTMENT, "Adjustment"),
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
        related_name="vendor_transactions",
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="transactions",
        null=True,
        blank=True,
    )

    transaction_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    transaction_date = models.DateField(default=timezone.localdate)
    number = models.CharField(max_length=80, blank=True)
    po_number = models.CharField(max_length=80, blank=True)

    debit_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="vendor_debit_transactions",
    )
    credit_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="vendor_credit_transactions",
    )

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    memo = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED)

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vendor_transaction",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-id"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"

    @property
    def debit_amount(self):
        if self.transaction_type == self.TYPE_VENDOR_PAYMENT:
            return self.amount
        return Decimal("0.00")

    @property
    def credit_amount(self):
        if self.transaction_type in [self.TYPE_PURCHASE_ORDER, self.TYPE_ADJUSTMENT]:
            return self.amount
        return Decimal("0.00")
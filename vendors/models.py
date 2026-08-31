from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import Company
from accounting.models import ChartOfAccount, JournalEntry
from stock.models import Item


class Vendor(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="vendors",
    )

    code = models.CharField(max_length=80, blank=True, db_index=True)
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
        return f"{self.code} - {self.name}" if self.code else self.name

    @property
    def ap_balance(self):
        legacy_transactions = self.transactions.filter(
            status=VendorTransaction.STATUS_POSTED,
            company=self.company,
        )

        legacy_credit = legacy_transactions.filter(
            transaction_type__in=[
                VendorTransaction.TYPE_PURCHASE_ORDER,
                VendorTransaction.TYPE_ADJUSTMENT,
            ]
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

        legacy_debit = legacy_transactions.filter(
            transaction_type=VendorTransaction.TYPE_VENDOR_PAYMENT
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

        new_bills = self.purchase_bills.filter(
            company=self.company,
            status=PurchaseBill.STATUS_POSTED,
        ).aggregate(total=models.Sum("total_amount"))["total"] or Decimal("0.00")

        return self.opening_balance + legacy_credit + new_bills - legacy_debit


class VendorTransaction(models.Model):
    """Legacy single-line vendor transaction.

    Kept for backward compatibility and existing historical data. New Purchase Bills
    are stored in PurchaseBill + line models below.
    """

    TYPE_PURCHASE_ORDER = "purchase_order"
    TYPE_CASH_EXPENSE = "cash_expense"
    TYPE_VENDOR_PAYMENT = "vendor_payment"
    TYPE_ADJUSTMENT = "adjustment"

    TYPE_CHOICES = [
        (TYPE_PURCHASE_ORDER, "Purchase Order / Bill (Legacy)"),
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


class PurchaseBill(models.Model):
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
        related_name="purchase_bills",
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="purchase_bills",
    )
    bill_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    number = models.CharField(max_length=80, blank=True)
    po_number = models.CharField(max_length=80, blank=True)

    accounts_payable_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="purchase_bills_ap",
        help_text="Normally Accounts Payable.",
    )
    input_vat_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_bills_input_vat",
        help_text="Required only when VAT amount is entered.",
    )

    memo = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    vat_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_bill",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-bill_date", "-id"]

    def __str__(self):
        return f"{self.number or f'PB-{self.pk}'} - {self.vendor}"

    def recalculate_totals(self, save=True):
        item_subtotal = self.item_lines.aggregate(total=models.Sum("line_amount"))["total"] or Decimal("0.00")
        expense_subtotal = self.expense_lines.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
        item_vat = self.item_lines.aggregate(total=models.Sum("vat_amount"))["total"] or Decimal("0.00")
        expense_vat = self.expense_lines.aggregate(total=models.Sum("vat_amount"))["total"] or Decimal("0.00")

        self.subtotal = item_subtotal + expense_subtotal
        self.vat_total = item_vat + expense_vat
        self.total_amount = self.subtotal + self.vat_total

        if save:
            self.save(update_fields=["subtotal", "vat_total", "total_amount", "updated_at"])

        return self.total_amount

    def clean(self):
        if self.vendor_id and self.company_id and self.vendor.company_id != self.company_id:
            raise ValidationError("Vendor must belong to the selected company.")
        for field_name in ("accounts_payable_account", "input_vat_account"):
            account = getattr(self, field_name, None)
            if account and self.company_id and account.company_id != self.company_id:
                raise ValidationError({field_name: "Account must belong to the selected company."})


class PurchaseBillItemLine(models.Model):
    bill = models.ForeignKey(PurchaseBill, on_delete=models.CASCADE, related_name="item_lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="purchase_bill_lines")
    description = models.CharField(max_length=255, blank=True)
    qty = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit_name = models.CharField(max_length=50, blank=True)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_bill_item_lines",
        help_text="Defaults to the item's Inventory Account when blank.",
    )
    vat_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.line_amount = (self.qty or Decimal("0.00")) * (self.unit_cost or Decimal("0.00"))
        if not self.unit_name and self.item_id and self.item.unit_set_id:
            self.unit_name = self.item.unit_set.default_purchase or self.item.unit_set.base_unit
        if not self.account_id and self.item_id:
            self.account = self.item.inventory_account
        super().save(*args, **kwargs)

    def clean(self):
        if self.item_id and self.bill_id and self.item.company_id != self.bill.company_id:
            raise ValidationError("Item must belong to the selected company.")
        if self.account_id and self.bill_id and self.account.company_id != self.bill.company_id:
            raise ValidationError("Account must belong to the selected company.")
        if self.qty is not None and self.qty <= 0:
            raise ValidationError({"qty": "Quantity must be more than zero."})
        if self.unit_cost is not None and self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.vat_amount is not None and self.vat_amount < 0:
            raise ValidationError({"vat_amount": "VAT cannot be negative."})


class PurchaseBillExpenseLine(models.Model):
    bill = models.ForeignKey(PurchaseBill, on_delete=models.CASCADE, related_name="expense_lines")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="purchase_bill_expense_lines",
    )
    vat_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.account_id and self.bill_id and self.account.company_id != self.bill.company_id:
            raise ValidationError("Account must belong to the selected company.")
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be more than zero."})
        if self.vat_amount is not None and self.vat_amount < 0:
            raise ValidationError({"vat_amount": "VAT cannot be negative."})
# =========================================================
# CUSTOMER REQUIREMENT PAYMENT (Apply to Invoices / Other Charge)
# =========================================================
class VendorPayment(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_POSTED = "posted"
    STATUS_VOID = "void"
    STATUS_CHOICES = [(STATUS_DRAFT, "Draft"), (STATUS_POSTED, "Posted"), (STATUS_VOID, "Void")]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="vendor_payments")
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="payments")
    payment_date = models.DateField(default=timezone.localdate)
    number = models.CharField(max_length=80, blank=True)
    payment_method = models.CharField(max_length=80, blank=True, default="Cash")
    payment_account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT, related_name="vendor_payment_cash_accounts")
    accounts_payable_account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT, related_name="vendor_payment_ap_accounts")
    currency = models.CharField(max_length=20, default="USD")
    memo = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED)
    journal_entry = models.OneToOneField(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name="vendor_payment")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]

    def recalculate_total(self, save=True):
        allocations = self.allocations.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
        charges = self.other_charges.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
        self.total_amount = allocations + charges
        if save:
            self.save(update_fields=["total_amount"])
        return self.total_amount


class VendorPaymentAllocation(models.Model):
    payment = models.ForeignKey(VendorPayment, on_delete=models.CASCADE, related_name="allocations")
    bill = models.ForeignKey(PurchaseBill, on_delete=models.PROTECT, related_name="payment_allocations")
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    memo = models.CharField(max_length=255, blank=True)


class VendorPaymentOtherCharge(models.Model):
    payment = models.ForeignKey(VendorPayment, on_delete=models.CASCADE, related_name="other_charges")
    memo = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT, related_name="vendor_payment_other_charges")

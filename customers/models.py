from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounting.models import ChartOfAccount, JournalEntry
from core.models import Company


class CustomerType(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="customer_types")
    name = models.CharField(max_length=120)
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit_term = models.PositiveIntegerField(default=0, help_text="Credit term in days")
    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class Salesperson(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="salespersons")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, blank=True)
    local_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class PriceLevel(models.Model):
    MODE_PERCENTAGE = "percentage"
    MODE_FIXED = "fixed"

    MODE_CHOICES = [
        (MODE_PERCENTAGE, "Percentage"),
        (MODE_FIXED, "Fixed Value"),
    ]

    TYPE_SALE = "sale"
    TYPE_DISCOUNT = "discount"

    TYPE_CHOICES = [
        (TYPE_SALE, "Sale Price"),
        (TYPE_DISCOUNT, "Discount"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="price_levels")
    name = models.CharField(max_length=120)
    mode = models.CharField(max_length=30, choices=MODE_CHOICES, default=MODE_PERCENTAGE)
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    round_type = models.CharField(max_length=80, blank=True)
    discount_method = models.CharField(max_length=80, blank=True)
    price_level_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_SALE)
    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class Region(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="regions")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, blank=True)
    local_name = models.CharField(max_length=120, blank=True)
    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="customers")

    name = models.CharField(max_length=180)
    code = models.CharField(max_length=80, blank=True)
    local_name = models.CharField(max_length=180, blank=True)

    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    telegram = models.CharField(max_length=120, blank=True)
    address = models.TextField(blank=True)

    customer_type = models.ForeignKey(CustomerType, on_delete=models.SET_NULL, null=True, blank=True)
    salesperson = models.ForeignKey(Salesperson, on_delete=models.SET_NULL, null=True, blank=True)
    price_level = models.ForeignKey(PriceLevel, on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)

    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name

    @property
    def ar_balance(self):
        transactions = self.transactions.filter(status=CustomerTransaction.STATUS_POSTED)

        debit = transactions.aggregate(total=models.Sum("debit_amount"))["total"] or Decimal("0.00")
        credit = transactions.aggregate(total=models.Sum("credit_amount"))["total"] or Decimal("0.00")

        return self.opening_balance + debit - credit


class CustomerTransaction(models.Model):
    TYPE_INVOICE = "invoice"
    TYPE_RECEIVE_PAYMENT = "receive_payment"
    TYPE_CREDIT_NOTE = "credit_note"
    TYPE_ADJUSTMENT = "adjustment"

    TYPE_CHOICES = [
        (TYPE_INVOICE, "Invoice"),
        (TYPE_RECEIVE_PAYMENT, "Receive Payment"),
        (TYPE_CREDIT_NOTE, "Credit Note"),
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

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="customer_transactions")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="transactions")

    transaction_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    transaction_date = models.DateField(default=timezone.localdate)

    number = models.CharField(max_length=80, blank=True)
    so_number = models.CharField(max_length=80, blank=True)
    currency = models.CharField(max_length=20, default="USD")
    exchange_rate = models.DecimalField(max_digits=14, decimal_places=4, default=1)

    debit_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="customer_debit_transactions",
    )
    credit_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name="customer_credit_transactions",
    )

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    memo = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED)

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_transaction",
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-id"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.customer.name} - {self.amount}"

    @property
    def debit_amount(self):
        if self.transaction_type in [self.TYPE_INVOICE, self.TYPE_ADJUSTMENT]:
            return self.amount
        return Decimal("0.00")

    @property
    def credit_amount(self):
        if self.transaction_type in [self.TYPE_RECEIVE_PAYMENT, self.TYPE_CREDIT_NOTE]:
            return self.amount
        return Decimal("0.00")


class SalesDocument(models.Model):
    TYPE_QUOTATION = "quotation"
    TYPE_SALE_ORDER = "sale_order"

    TYPE_CHOICES = [
        (TYPE_QUOTATION, "Quotation"),
        (TYPE_SALE_ORDER, "Sale Order"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sales_documents")
    document_type = models.CharField(max_length=30, choices=TYPE_CHOICES)

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sales_documents")
    number = models.CharField(max_length=80, blank=True)
    document_date = models.DateField(default=timezone.localdate)
    delivery_date = models.DateField(null=True, blank=True)

    salesperson = models.ForeignKey(Salesperson, on_delete=models.SET_NULL, null=True, blank=True)
    customer_code = models.CharField(max_length=80, blank=True)
    address_name = models.CharField(max_length=180, blank=True)

    currency = models.CharField(max_length=20, default="USD")
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    memo = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-document_date", "-id"]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.number or self.id}"
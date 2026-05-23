from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Company
from accounting.models import ChartOfAccount, JournalEntry


class ItemGroup(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="item_groups")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, blank=True)
    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class ItemBrand(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="item_brands")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class UnitSet(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="unit_sets")
    name = models.CharField(max_length=120)
    base_unit = models.CharField(max_length=50, default="pcs")
    default_purchase = models.CharField(max_length=50, default="pcs")
    default_sale = models.CharField(max_length=50, default="pcs")
    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="warehouses")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, blank=True)
    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["company", "name"]

    def __str__(self):
        return self.name


class Item(models.Model):
    TYPE_STOCK_PART = "stock_part"
    TYPE_STOCK_ASSEMBLE = "stock_assemble"
    TYPE_SERVICE = "service"
    TYPE_PACKAGE = "package"

    ITEM_TYPE_CHOICES = [
        (TYPE_STOCK_PART, "Stock Part"),
        (TYPE_STOCK_ASSEMBLE, "Stock Assemble"),
        (TYPE_SERVICE, "Service"),
        (TYPE_PACKAGE, "Package"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="stock_items")
    code = models.CharField(max_length=80)
    name = models.CharField(max_length=180)

    item_type = models.CharField(max_length=30, choices=ITEM_TYPE_CHOICES, default=TYPE_STOCK_PART)
    item_group = models.ForeignKey(ItemGroup, on_delete=models.SET_NULL, null=True, blank=True)
    item_brand = models.ForeignKey(ItemBrand, on_delete=models.SET_NULL, null=True, blank=True)
    unit_set = models.ForeignKey(UnitSet, on_delete=models.SET_NULL, null=True, blank=True)

    cost_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    inventory_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_items",
        help_text="Usually Inventory Asset account",
    )
    cogs_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cogs_items",
        help_text="Usually Cost of Goods Sold account",
    )
    revenue_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revenue_items",
        help_text="Usually Sales Revenue account",
    )

    memo = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code", "name"]
        unique_together = ["company", "code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class StockDocument(models.Model):
    TYPE_ISSUE = "issue"
    TYPE_ADJUSTMENT = "adjustment"
    TYPE_ASSEMBLY = "assembly"
    TYPE_TRANSFER = "transfer"

    DOCUMENT_TYPE_CHOICES = [
        (TYPE_ISSUE, "Stock Issue"),
        (TYPE_ADJUSTMENT, "Stock Adjustment"),
        (TYPE_ASSEMBLY, "Stock Assembly"),
        (TYPE_TRANSFER, "Stock Transfer"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_POSTED = "posted"
    STATUS_VOID = "void"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_POSTED, "Posted"),
        (STATUS_VOID, "Void"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="stock_documents")
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    number = models.CharField(max_length=80, blank=True)
    document_date = models.DateField(default=timezone.localdate)

    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_docs")
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_transfers_from")
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_transfers_to")

    memo = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED)

    # For auto accounting journal.
    debit_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_debit_documents",
    )
    credit_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_credit_documents",
    )
    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_document",
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-document_date", "-id"]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.number or self.id}"

    @property
    def total_amount(self):
        total = self.lines.aggregate(total=models.Sum("amount"))["total"]
        return total or Decimal("0.00")


class StockDocumentLine(models.Model):
    document = models.ForeignKey(StockDocument, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="stock_lines")
    qty = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    memo = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["id"]

    @property
    def amount(self):
        return (self.qty or Decimal("0.00")) * (self.unit_cost or Decimal("0.00"))

    def __str__(self):
        return f"{self.item} x {self.qty}"
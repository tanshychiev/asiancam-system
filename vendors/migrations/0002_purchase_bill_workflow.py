from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("accounting", "0004_bulkimportlog_accountcustomer_accountitem"),
        ("stock", "0001_initial"),
        ("vendors", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="vendor",
            name="code",
            field=models.CharField(blank=True, db_index=True, max_length=80),
        ),
        migrations.CreateModel(
            name="PurchaseBill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bill_date", models.DateField(default=django.utils.timezone.localdate)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("number", models.CharField(blank=True, max_length=80)),
                ("po_number", models.CharField(blank=True, max_length=80)),
                ("memo", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("posted", "Posted"), ("void", "Void")], default="posted", max_length=20)),
                ("subtotal", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("vat_total", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("accounts_payable_account", models.ForeignKey(help_text="Normally Accounts Payable.", on_delete=django.db.models.deletion.PROTECT, related_name="purchase_bills_ap", to="accounting.chartofaccount")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="purchase_bills", to="core.company")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("input_vat_account", models.ForeignKey(blank=True, help_text="Required only when VAT amount is entered.", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="purchase_bills_input_vat", to="accounting.chartofaccount")),
                ("journal_entry", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="purchase_bill", to="accounting.journalentry")),
                ("vendor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="purchase_bills", to="vendors.vendor")),
            ],
            options={"ordering": ["-bill_date", "-id"]},
        ),
        migrations.CreateModel(
            name="PurchaseBillItemLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(blank=True, max_length=255)),
                ("qty", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("unit_name", models.CharField(blank=True, max_length=50)),
                ("unit_cost", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("line_amount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("vat_amount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("account", models.ForeignKey(blank=True, help_text="Defaults to the item's Inventory Account when blank.", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="purchase_bill_item_lines", to="accounting.chartofaccount")),
                ("bill", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="item_lines", to="vendors.purchasebill")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="purchase_bill_lines", to="stock.item")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="PurchaseBillExpenseLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=255)),
                ("amount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("vat_amount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="purchase_bill_expense_lines", to="accounting.chartofaccount")),
                ("bill", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expense_lines", to="vendors.purchasebill")),
            ],
            options={"ordering": ["id"]},
        ),
    ]

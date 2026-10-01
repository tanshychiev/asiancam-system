from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("customers", "0005_salesinvoiceline_credit_amount")]

    operations = [
        migrations.AlterField(
            model_name="salesinvoiceline",
            name="item",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="sales_invoice_lines", to="stock.item"),
        ),
        migrations.AddField(
            model_name="salesinvoiceline",
            name="discount_type",
            field=models.CharField(choices=[("fixed", "$"), ("percent", "%")], default="fixed", max_length=10),
        ),
        migrations.AddField(
            model_name="salesinvoiceline",
            name="discount_value",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name="salesinvoiceline",
            name="tax_rate",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
    ]

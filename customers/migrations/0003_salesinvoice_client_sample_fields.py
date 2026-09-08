from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0002_customer_requirement_documents"),
        ("stock", "0001_initial"),
    ]

    operations = [
        migrations.AddField(model_name="salesinvoice", name="quotation_no", field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name="salesinvoice", name="sale_order_no", field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name="salesinvoice", name="address_name", field=models.CharField(blank=True, max_length=180)),
        migrations.AddField(model_name="salesinvoice", name="truck_no", field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name="salesinvoice", name="credit_term", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="salesinvoice", name="discount_tax_mode", field=models.CharField(choices=[("before_tax", "Discount Before Tax"), ("after_tax", "Discount After Tax")], default="before_tax", max_length=20)),
        migrations.AddField(model_name="salesinvoice", name="price_level", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sales_invoices", to="customers.pricelevel")),
        migrations.AddField(model_name="salesinvoice", name="warehouse", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sales_invoices", to="stock.warehouse")),
    ]
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0004_salesinvoiceline_memo"),
    ]

    operations = [
        migrations.AddField(
            model_name="salesinvoiceline",
            name="credit_amount",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
        ),
    ]

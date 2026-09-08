from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0003_salesinvoice_client_sample_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="salesinvoiceline",
            name="memo",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]

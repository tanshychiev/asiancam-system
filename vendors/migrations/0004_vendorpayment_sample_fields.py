from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendors", "0003_vendor_payment_workflow"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendorpayment",
            name="cheque_to",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="vendorpayment",
            name="cheque_no",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="vendorpayment",
            name="reference",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]

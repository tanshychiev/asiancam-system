from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendors", "0004_vendorpayment_sample_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendorpaymentothercharge",
            name="tax_code",
            field=models.CharField(
                choices=[
                    ("NA", "NA"),
                    ("VAT10", "VAT 10%"),
                    ("VAT0", "VAT 0%"),
                    ("EXEMPT", "Tax Exempt"),
                ],
                default="NA",
                max_length=20,
            ),
        ),
    ]

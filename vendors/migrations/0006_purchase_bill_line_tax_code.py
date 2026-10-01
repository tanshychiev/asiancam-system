from django.db import migrations, models


def infer_old_tax_codes(apps, schema_editor):
    ItemLine = apps.get_model('vendors', 'PurchaseBillItemLine')
    ExpenseLine = apps.get_model('vendors', 'PurchaseBillExpenseLine')
    ItemLine.objects.filter(vat_amount__gt=0).update(tax_code='VAT10')
    ExpenseLine.objects.filter(vat_amount__gt=0).update(tax_code='VAT10')


class Migration(migrations.Migration):
    dependencies = [
        ('vendors', '0005_vendorpaymentothercharge_tax_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasebillitemline',
            name='tax_code',
            field=models.CharField(
                choices=[('NA', 'N/A'), ('VAT0', 'VAT 0%'), ('VAT10', 'VAT 10%')],
                default='NA',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='purchasebillexpenseline',
            name='tax_code',
            field=models.CharField(
                choices=[('NA', 'N/A'), ('VAT0', 'VAT 0%'), ('VAT10', 'VAT 10%')],
                default='NA',
                max_length=20,
            ),
        ),
        migrations.RunPython(infer_old_tax_codes, migrations.RunPython.noop),
    ]
